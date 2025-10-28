import json
import boto3
import time
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, RequestError
import pprint
import warnings
warnings.filterwarnings('ignore')

embedding_context_dimensions = {
    "amazon.titan-embed-text-v2:0": 1024
}

pp = pprint.PrettyPrinter(indent=2)

def interactive_sleep(seconds: int):
    """Simple sleep with progress indicator"""
    for i in range(seconds):
        print(f"Waiting... {i+1}/{seconds}", end='\r')
        time.sleep(1)
    print()

class BedrockKnowledgeBase:
    """
    Simplified Knowledge Base class for creating and syncing data from S3 bucket
    """
    def __init__(
            self,
            kb_name,
            kb_description,
            s3_bucket_name,
            embedding_model="amazon.titan-embed-text-v2:0",
            chunking_strategy="FIXED_SIZE",
            suffix=None
    ):
        """
        Initialize simplified Knowledge Base
        Args:
            kb_name(str): The name of the Knowledge Base
            kb_description(str): The description of the Knowledge Base
            s3_bucket_name(str): The S3 bucket containing the data
            embedding_model(str): The embedding model to use
            chunking_strategy(str): The chunking strategy
            suffix(str): A suffix for naming resources
        """
        boto3_session = boto3.session.Session()
        self.region_name = boto3_session.region_name
        self.iam_client = boto3_session.client('iam')
        self.account_number = boto3.client('sts').get_caller_identity().get('Account')
        self.suffix = suffix or f'{self.region_name}-{self.account_number}'
        self.identity = boto3.client('sts').get_caller_identity()['Arn']
        self.aoss_client = boto3_session.client('opensearchserverless')
        self.s3_client = boto3.client('s3')
        self.bedrock_agent_client = boto3.client('bedrock-agent')
        self.ssm_client = boto3.client('ssm')
        credentials = boto3.Session().get_credentials()
        self.awsauth = AWSV4SignerAuth(credentials, self.region_name, 'aoss')

        self.kb_name = kb_name
        self.kb_description = kb_description
        self.s3_bucket_name = s3_bucket_name
        self.embedding_model = embedding_model
        self.chunking_strategy = chunking_strategy
        
        # Resource names
        self.encryption_policy_name = f"bedrock-kb-sp-{self.suffix}"
        self.network_policy_name = f"bedrock-kb-np-{self.suffix}"
        self.access_policy_name = f'bedrock-kb-ap-{self.suffix}'
        self.kb_execution_role_name = f'BedrockKBExecutionRole-{self.suffix}'
        self.fm_policy_name = f'BedrockKBFoundationModelPolicy-{self.suffix}'
        self.s3_policy_name = f'BedrockKBS3Policy-{self.suffix}'
        self.oss_policy_name = f'BedrockKBOSSPolicy-{self.suffix}'
        
        self.vector_store_name = f'bedrock-kb-{self.suffix}'
        self.index_name = f"bedrock-kb-index-{self.suffix}"
        
        # Parameter Store path for saving KB ID
        self.parameter_name = f"/bedrock/knowledge-base/{self.kb_name}/kb-id"

        self._setup_resources()

    def _setup_resources(self):
        print("Setting up Knowledge Base resources...")
        
        print("Step 1 - Creating IAM execution role and policies")
        self.bedrock_kb_execution_role = self.create_execution_role()
        
        # Wait for IAM role to propagate
        print("Waiting for IAM role to propagate...")
        interactive_sleep(30)
        
        print("Step 2 - Creating OpenSearch Serverless policies")
        self.encryption_policy, self.network_policy, self.access_policy = self.create_oss_policies()
        
        print("Step 3 - Creating OpenSearch Serverless collection")
        self.host, self.collection, self.collection_id, self.collection_arn = self.create_oss_collection()
        
        print("Step 4 - Creating vector index")
        self.create_vector_index()
        
        print("Step 5 - Verifying setup and creating Knowledge Base")
        self.verify_permissions()
        self.verify_index_ready()
        self.knowledge_base, self.data_source = self.create_knowledge_base()
        
        print("Knowledge Base setup complete!")
        
    def verify_s3_bucket(self):
        """Verify that the S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
            print(f'S3 bucket {self.s3_bucket_name} exists and is accessible')
            return True
        except ClientError as e:
            print(f'Error accessing S3 bucket {self.s3_bucket_name}: {e}')
            return False

    def create_execution_role(self):
        """Create simplified IAM execution role for Knowledge Base"""
        # Foundation model policy
        foundation_model_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": f"arn:aws:bedrock:{self.region_name}::foundation-model/{self.embedding_model}"
                }
            ]
        }

        # S3 policy for the data bucket
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:ListBucket"],
                    "Resource": [
                        f"arn:aws:s3:::{self.s3_bucket_name}",
                        f"arn:aws:s3:::{self.s3_bucket_name}/*"
                    ]
                }
            ]
        }

        # Trust policy for Bedrock service
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        try:
            # Create the execution role
            role_response = self.iam_client.create_role(
                RoleName=self.kb_execution_role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Bedrock Knowledge Base Execution Role'
            )
            print(f"Created IAM role: {self.kb_execution_role_name}")
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            role_response = self.iam_client.get_role(RoleName=self.kb_execution_role_name)
            print(f"Using existing IAM role: {self.kb_execution_role_name}")

        # Create and attach policies
        policies = [
            (self.fm_policy_name, foundation_model_policy),
            (self.s3_policy_name, s3_policy)
        ]

        for policy_name, policy_document in policies:
            try:
                policy_response = self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                policy_arn = policy_response['Policy']['Arn']
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                policy_arn = f"arn:aws:iam::{self.account_number}:policy/{policy_name}"

            self.iam_client.attach_role_policy(
                RoleName=self.kb_execution_role_name,
                PolicyArn=policy_arn
            )

        return role_response

    def create_oss_policies(self):
        """Create OpenSearch Serverless security policies"""
        try:
            encryption_policy = self.aoss_client.create_security_policy(
                name=self.encryption_policy_name,
                policy=json.dumps({
                    'Rules': [{'Resource': ['collection/' + self.vector_store_name],
                               'ResourceType': 'collection'}],
                    'AWSOwnedKey': True
                }),
                type='encryption'
            )
        except self.aoss_client.exceptions.ConflictException:
            encryption_policy = self.aoss_client.get_security_policy(
                name=self.encryption_policy_name, type='encryption')

        try:
            network_policy = self.aoss_client.create_security_policy(
                name=self.network_policy_name,
                policy=json.dumps([{
                    'Rules': [{'Resource': ['collection/' + self.vector_store_name],
                               'ResourceType': 'collection'}],
                    'AllowFromPublic': True
                }]),
                type='network'
            )
        except self.aoss_client.exceptions.ConflictException:
            network_policy = self.aoss_client.get_security_policy(
                name=self.network_policy_name, type='network')

        try:
            # Create access policy with comprehensive permissions
            access_policy_document = [{
                'Rules': [
                    {
                        'Resource': ['collection/' + self.vector_store_name],
                        'Permission': [
                            'aoss:CreateCollectionItems',
                            'aoss:DeleteCollectionItems', 
                            'aoss:UpdateCollectionItems',
                            'aoss:DescribeCollectionItems'
                        ],
                        'ResourceType': 'collection'
                    },
                    {
                        'Resource': ['index/' + self.vector_store_name + '/*'],
                        'Permission': [
                            'aoss:CreateIndex',
                            'aoss:DeleteIndex',
                            'aoss:UpdateIndex', 
                            'aoss:DescribeIndex',
                            'aoss:ReadDocument',
                            'aoss:WriteDocument'
                        ],
                        'ResourceType': 'index'
                    }
                ],
                'Principal': [self.identity, self.bedrock_kb_execution_role['Role']['Arn']],
                'Description': f'Data access policy for {self.vector_store_name}'
            }]
            
            access_policy = self.aoss_client.create_access_policy(
                name=self.access_policy_name,
                policy=json.dumps(access_policy_document),
                type='data'
            )
            print(f"Created access policy: {self.access_policy_name}")
        except self.aoss_client.exceptions.ConflictException:
            access_policy = self.aoss_client.get_access_policy(
                name=self.access_policy_name, type='data')
            print(f"Using existing access policy: {self.access_policy_name}")

        return encryption_policy, network_policy, access_policy

    def create_oss_collection(self):
        """Create OpenSearch Serverless collection"""
        try:
            collection = self.aoss_client.create_collection(
                name=self.vector_store_name, 
                type='VECTORSEARCH'
            )
            collection_id = collection['createCollectionDetail']['id']
            collection_arn = collection['createCollectionDetail']['arn']
            print(f"Created new collection: {self.vector_store_name}")
        except self.aoss_client.exceptions.ConflictException:
            collection = self.aoss_client.batch_get_collection(names=[self.vector_store_name])['collectionDetails'][0]
            collection_id = collection['id']
            collection_arn = collection['arn']
            print(f"Using existing collection: {self.vector_store_name}")

        host = f"{collection_id}.{self.region_name}.aoss.amazonaws.com"

        # Wait for collection to be active
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            response = self.aoss_client.batch_get_collection(names=[self.vector_store_name])
            status = response['collectionDetails'][0]['status']
            if status == 'ACTIVE':
                print(f"Collection is now active: {self.vector_store_name}")
                break
            elif status == 'FAILED':
                raise Exception(f"Collection creation failed: {self.vector_store_name}")
            
            attempt += 1
            print(f"Collection status: {status}, waiting... (attempt {attempt}/{max_attempts})")
            interactive_sleep(30)
        
        if attempt >= max_attempts:
            raise Exception(f"Collection did not become active within expected time: {self.vector_store_name}")

        # Create OSS policy for Bedrock execution role
        self.create_oss_execution_policy(collection_id)
        
        # Wait for policies to propagate
        print("Waiting for access policies to propagate...")
        interactive_sleep(60)
        
        # Initialize OpenSearch client
        self.oss_client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )
        
        # Verify collection is accessible
        self.verify_oss_access()

        return host, collection, collection_id, collection_arn

    def create_oss_execution_policy(self, collection_id):
        """Create and attach OpenSearch Serverless policy to execution role"""
        oss_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["aoss:APIAccessAll"],
                    "Resource": f"arn:aws:aoss:{self.region_name}:{self.account_number}:collection/{collection_id}"
                }
            ]
        }
        
        try:
            oss_policy = self.iam_client.create_policy(
                PolicyName=self.oss_policy_name,
                PolicyDocument=json.dumps(oss_policy_document)
            )
            oss_policy_arn = oss_policy["Policy"]["Arn"]
            print(f"Created OSS execution policy: {self.oss_policy_name}")
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            oss_policy_arn = f"arn:aws:iam::{self.account_number}:policy/{self.oss_policy_name}"
            print(f"Using existing OSS execution policy: {self.oss_policy_name}")

        self.iam_client.attach_role_policy(
            RoleName=self.bedrock_kb_execution_role["Role"]["RoleName"],
            PolicyArn=oss_policy_arn
        )

    def verify_oss_access(self):
        """Verify OpenSearch Serverless collection is accessible"""
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                # Try to get cluster info
                response = self.oss_client.info()
                print(f"✓ OpenSearch collection is accessible: {response.get('version', {}).get('number', 'unknown')}")
                return True
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"Collection access attempt {attempt + 1}/{max_attempts} failed, retrying...")
                    interactive_sleep(30)
                else:
                    print(f"⚠ Collection access verification failed after {max_attempts} attempts: {e}")
                    print("Proceeding anyway - this may cause issues during Knowledge Base creation")
                    return False
        return False

    def verify_permissions(self):
        """Verify that all necessary permissions are in place"""
        print("Verifying permissions...")
        
        # Check if IAM role exists and has policies attached
        try:
            role_policies = self.iam_client.list_attached_role_policies(
                RoleName=self.kb_execution_role_name
            )
            policy_count = len(role_policies['AttachedPolicies'])
            print(f"✓ IAM role has {policy_count} policies attached")
            
            if policy_count < 2:  # Should have at least foundation model and S3 policies
                print("⚠ Warning: IAM role may not have sufficient policies")
                
        except Exception as e:
            print(f"⚠ Warning: Could not verify IAM role policies: {e}")
        
        # Check if OpenSearch collection is accessible
        try:
            collection_response = self.aoss_client.batch_get_collection(names=[self.vector_store_name])
            collection_status = collection_response['collectionDetails'][0]['status']
            if collection_status == 'ACTIVE':
                print("✓ OpenSearch collection is active")
            else:
                print(f"⚠ Warning: OpenSearch collection status is {collection_status}")
        except Exception as e:
            print(f"⚠ Warning: Could not verify OpenSearch collection: {e}")
        
        # Check if S3 bucket is accessible
        if self.verify_s3_bucket():
            print("✓ S3 bucket is accessible")
        else:
            print("⚠ Warning: S3 bucket may not be accessible")
        
        print("Permission verification completed")

    def verify_index_ready(self):
        """Verify that the vector index is ready for Knowledge Base creation"""
        print("Verifying vector index is ready...")
        
        if not self.verify_index_exists():
            print("✗ Vector index does not exist!")
            raise Exception(f"Vector index {self.index_name} not found. Cannot create Knowledge Base.")
        
        print(f"✓ Vector index {self.index_name} is ready")
        
        print("Vector index verification completed")

    def create_vector_index(self):
        """Create OpenSearch Serverless vector index with proper verification"""
        print(f"Creating vector index: {self.index_name}")
        
        # First check if index already exists
        if self.verify_index_exists():
            print(f"Vector index {self.index_name} already exists")
            return True
        
        index_body = {
            "settings": {
                "index.knn": "true",
                "number_of_shards": 1,
                "knn.algo_param.ef_search": 512,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "vector": {
                        "type": "knn_vector",
                        "dimension": embedding_context_dimensions[self.embedding_model],
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "space_type": "l2"
                        },
                    },
                    "text": {"type": "text"},
                    "text-metadata": {"type": "text"}
                }
            }
        }

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.oss_client.indices.create(
                    index=self.index_name, 
                    body=json.dumps(index_body)
                )
                print(f"✓ Created vector index: {self.index_name}")
                
                # Wait for index to be ready
                print("Waiting for index to be ready...")
                interactive_sleep(30)
                
                # Verify index was created successfully
                if self.verify_index_exists():
                    print("✓ Vector index verified successfully")
                    return True
                else:
                    print("⚠ Index creation may not be complete, retrying...")
                    if attempt < max_attempts - 1:
                        interactive_sleep(30)
                        continue
                    
            except RequestError as e:
                error_str = str(e)
                if 'resource_already_exists_exception' in error_str:
                    print(f"Vector index {self.index_name} already exists")
                    return True
                elif 'security_exception' in error_str or '403' in error_str:
                    if attempt < max_attempts - 1:
                        print(f"Access denied creating index (attempt {attempt + 1}/{max_attempts}), waiting for permissions...")
                        interactive_sleep(60)
                        continue
                    else:
                        print(f"✗ Failed to create index after {max_attempts} attempts due to permissions")
                        raise e
                else:
                    print(f'✗ Error creating index: {e}')
                    if attempt < max_attempts - 1:
                        print(f"Retrying index creation (attempt {attempt + 2}/{max_attempts})...")
                        interactive_sleep(30)
                        continue
                    else:
                        raise e
            except Exception as e:
                print(f'✗ Unexpected error creating index: {e}')
                if attempt < max_attempts - 1:
                    print(f"Retrying index creation (attempt {attempt + 2}/{max_attempts})...")
                    interactive_sleep(30)
                    continue
                else:
                    raise e
        
        # Final verification
        if self.verify_index_exists():
            print("✓ Vector index creation completed successfully")
            return True
        else:
            raise Exception(f"Failed to create or verify vector index: {self.index_name}")

    def verify_index_exists(self):
        """Verify that the vector index exists and is accessible"""
        try:
            response = self.oss_client.indices.exists(index=self.index_name)
            return response
        except Exception as e:
            print(f"Could not verify index existence: {e}")
            return False



    def get_chunking_config(self):
        """Get chunking configuration for the knowledge base"""
        if self.chunking_strategy == "FIXED_SIZE":
            return {
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 300,
                        "overlapPercentage": 20
                    }
                }
            }
        else:
            return {"chunkingConfiguration": {"chunkingStrategy": "NONE"}}

    def create_knowledge_base(self):
        """Create Knowledge Base and S3 data source"""
        # Storage configuration for OpenSearch Serverless
        storage_configuration = {
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": self.collection_arn,
                "vectorIndexName": self.index_name,
                "fieldMapping": {
                    "vectorField": "vector",
                    "textField": "text",
                    "metadataField": "text-metadata"
                }
            }
        }

        # Knowledge base configuration
        embedding_model_arn = f"arn:aws:bedrock:{self.region_name}::foundation-model/{self.embedding_model}"
        kb_configuration = {
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": embedding_model_arn
            }
        }

        # Create Knowledge Base with retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                create_kb_response = self.bedrock_agent_client.create_knowledge_base(
                    name=self.kb_name,
                    description=self.kb_description,
                    roleArn=self.bedrock_kb_execution_role['Role']['Arn'],
                    knowledgeBaseConfiguration=kb_configuration,
                    storageConfiguration=storage_configuration,
                )
                kb = create_kb_response["knowledgeBase"]
                print(f"Created Knowledge Base: {self.kb_name}")
                break
            except self.bedrock_agent_client.exceptions.ConflictException:
                # Knowledge base already exists, retrieve it
                kbs = self.bedrock_agent_client.list_knowledge_bases(maxResults=100)
                kb_id = next((kb['knowledgeBaseId'] for kb in kbs['knowledgeBaseSummaries'] 
                             if kb['name'] == self.kb_name), None)
                if kb_id:
                    response = self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=kb_id)
                    kb = response['knowledgeBase']
                    print(f"Using existing Knowledge Base: {self.kb_name}")
                    break
                else:
                    raise Exception(f"Knowledge Base {self.kb_name} not found")
            except Exception as e:
                if "security_exception" in str(e) or "403" in str(e):
                    if attempt < max_attempts - 1:
                        print(f"Access denied (attempt {attempt + 1}/{max_attempts}). Waiting for permissions to propagate...")
                        interactive_sleep(60)
                        continue
                    else:
                        print(f"Failed to create Knowledge Base after {max_attempts} attempts due to access issues.")
                        print("This usually indicates:")
                        print("1. OpenSearch Serverless access policies need more time to propagate")
                        print("2. IAM role permissions are insufficient")
                        print("3. Collection is not properly accessible")
                        raise e
                elif "no such index" in str(e).lower():
                    print(f"✗ Vector index {self.index_name} not found!")
                    print("This usually means:")
                    print("1. Index creation failed silently")
                    print("2. Index was created in wrong collection")
                    print("3. Timing issue - index not ready yet")
                    
                    if attempt < max_attempts - 1:
                        print(f"\nTrying to recreate the index (attempt {attempt + 1}/{max_attempts})...")
                        try:
                            self.create_vector_index()
                            print("Index recreated, retrying Knowledge Base creation...")
                            interactive_sleep(30)
                            continue
                        except Exception as index_error:
                            print(f"Failed to recreate index: {index_error}")
                            if attempt == max_attempts - 2:  # Last attempt
                                raise e
                            continue
                    else:
                        raise e
                else:
                    raise e

        # Create S3 data source
        data_source = self.create_s3_data_source(kb['knowledgeBaseId'])
        
        # Save Knowledge Base ID to Parameter Store
        self.save_kb_id_to_parameter_store(kb['knowledgeBaseId'])
        
        return kb, data_source
    
    def create_s3_data_source(self, kb_id):
        """Create S3 data source for the Knowledge Base"""
        data_source_config = {
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{self.s3_bucket_name}"
            }
        }

        vector_ingestion_config = self.get_chunking_config()

        try:
            create_ds_response = self.bedrock_agent_client.create_data_source(
                name=f"{self.kb_name}-s3-source",
                description=f"S3 data source for {self.kb_name}",
                knowledgeBaseId=kb_id,
                dataSourceConfiguration=data_source_config,
                vectorIngestionConfiguration=vector_ingestion_config
            )
            data_source = create_ds_response["dataSource"]
            print(f"Created S3 data source for bucket: {self.s3_bucket_name}")
            return data_source
        except self.bedrock_agent_client.exceptions.ConflictException:
            # Data source already exists, retrieve it
            ds_list = self.bedrock_agent_client.list_data_sources(
                knowledgeBaseId=kb_id,
                maxResults=100
            )['dataSourceSummaries']
            
            if ds_list:
                ds_id = ds_list[0]['dataSourceId']
                get_ds_response = self.bedrock_agent_client.get_data_source(
                    dataSourceId=ds_id,
                    knowledgeBaseId=kb_id
                )
                data_source = get_ds_response["dataSource"]
                print(f"Using existing S3 data source for bucket: {self.s3_bucket_name}")
                return data_source
            else:
                raise Exception("No data sources found for Knowledge Base")
        

    def start_ingestion_job(self):
        """Start data ingestion job to sync S3 data to Knowledge Base"""
        try:
            start_job_response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=self.knowledge_base['knowledgeBaseId'],
                dataSourceId=self.data_source["dataSourceId"]
            )
            job = start_job_response["ingestionJob"]
            print(f"Started ingestion job: {job['ingestionJobId']}")
            
            # Wait for job completion
            while job['status'] not in ["COMPLETE", "FAILED", "STOPPED"]:
                print(f"Ingestion job status: {job['status']}")
                interactive_sleep(30)
                
                get_job_response = self.bedrock_agent_client.get_ingestion_job(
                    knowledgeBaseId=self.knowledge_base['knowledgeBaseId'],
                    dataSourceId=self.data_source["dataSourceId"],
                    ingestionJobId=job["ingestionJobId"]
                )
                job = get_job_response["ingestionJob"]
            
            print(f"Ingestion job completed with status: {job['status']}")
            if job['status'] == 'FAILED':
                print(f"Failure reason: {job.get('failureReasons', 'Unknown')}")
            
            return job
            
        except Exception as e:
            print(f"Error starting ingestion job: {e}")
            raise
            

    def save_kb_id_to_parameter_store(self, kb_id):
        """Save Knowledge Base ID to AWS Systems Manager Parameter Store"""
        try:
            # Define tags for the parameter
            tags = [
                {
                    'Key': 'KnowledgeBaseName',
                    'Value': self.kb_name
                },
                {
                    'Key': 'S3Bucket',
                    'Value': self.s3_bucket_name
                },
                {
                    'Key': 'CreatedBy',
                    'Value': 'BedrockKnowledgeBase'
                }
            ]
            
            # Check if parameter already exists
            try:
                self.ssm_client.get_parameter(Name=self.parameter_name)
                parameter_exists = True
            except self.ssm_client.exceptions.ParameterNotFound:
                parameter_exists = False
            
            if parameter_exists:
                # Parameter exists - update value only (can't use tags with overwrite)
                self.ssm_client.put_parameter(
                    Name=self.parameter_name,
                    Value=kb_id,
                    Type='String',
                    Description=f'Knowledge Base ID for {self.kb_name}',
                    Overwrite=True
                )
                print(f"Updated existing parameter: {self.parameter_name}")
                
                # Update tags separately
                try:
                    # Remove existing tags first
                    existing_tags = self.ssm_client.list_tags_for_resource(
                        ResourceType='Parameter',
                        ResourceId=self.parameter_name
                    )
                    if existing_tags.get('TagList'):
                        tag_keys = [tag['Key'] for tag in existing_tags['TagList']]
                        self.ssm_client.remove_tags_from_resource(
                            ResourceType='Parameter',
                            ResourceId=self.parameter_name,
                            TagKeys=tag_keys
                        )
                    
                    # Add new tags
                    self.ssm_client.add_tags_to_resource(
                        ResourceType='Parameter',
                        ResourceId=self.parameter_name,
                        Tags=tags
                    )
                    print("Updated parameter tags")
                except Exception as tag_error:
                    print(f"Warning: Could not update tags: {tag_error}")
                    
            else:
                # Parameter doesn't exist - create new with tags (no overwrite flag)
                self.ssm_client.put_parameter(
                    Name=self.parameter_name,
                    Value=kb_id,
                    Type='String',
                    Description=f'Knowledge Base ID for {self.kb_name}',
                    Tags=tags
                )
                print(f"Created new parameter: {self.parameter_name}")
            
            print(f"Saved Knowledge Base ID to Parameter Store: {self.parameter_name}")
            return True
            
        except Exception as e:
            print(f"Error saving KB ID to Parameter Store: {e}")
            return False

    def get_kb_id_from_parameter_store(self):
        """Retrieve Knowledge Base ID from AWS Systems Manager Parameter Store"""
        try:
            response = self.ssm_client.get_parameter(Name=self.parameter_name)
            kb_id = response['Parameter']['Value']
            print(f"Retrieved Knowledge Base ID from Parameter Store: {kb_id}")
            return kb_id
        except self.ssm_client.exceptions.ParameterNotFound:
            print(f"Parameter {self.parameter_name} not found in Parameter Store")
            return None
        except Exception as e:
            print(f"Error retrieving KB ID from Parameter Store: {e}")
            return None

    @classmethod
    def get_kb_id_by_name(cls, kb_name, region_name=None):
        """Class method to retrieve Knowledge Base ID by name from Parameter Store"""
        if not region_name:
            region_name = boto3.session.Session().region_name
        
        ssm_client = boto3.client('ssm', region_name=region_name)
        parameter_name = f"/bedrock/knowledge-base/{kb_name}/kb-id"
        
        try:
            response = ssm_client.get_parameter(Name=parameter_name)
            kb_id = response['Parameter']['Value']
            print(f"Retrieved Knowledge Base ID for '{kb_name}': {kb_id}")
            return kb_id
        except ssm_client.exceptions.ParameterNotFound:
            print(f"Knowledge Base '{kb_name}' not found in Parameter Store")
            return None
        except Exception as e:
            print(f"Error retrieving KB ID for '{kb_name}': {e}")
            return None

    def list_saved_knowledge_bases(self):
        """List all saved Knowledge Base IDs from Parameter Store"""
        try:
            response = self.ssm_client.get_parameters_by_path(
                Path="/bedrock/knowledge-base/",
                Recursive=True
            )
            
            kb_list = []
            for param in response['Parameters']:
                if param['Name'].endswith('/kb-id'):
                    kb_name = param['Name'].split('/')[-2]
                    kb_list.append({
                        'name': kb_name,
                        'kb_id': param['Value'],
                        'parameter_name': param['Name'],
                        'last_modified': param['LastModifiedDate']
                    })
            
            if kb_list:
                print("Saved Knowledge Bases:")
                for kb in kb_list:
                    print(f"  - {kb['name']}: {kb['kb_id']}")
            else:
                print("No saved Knowledge Bases found in Parameter Store")
            
            return kb_list
            
        except Exception as e:
            print(f"Error listing Knowledge Bases from Parameter Store: {e}")
            return []

    def get_knowledge_base_id(self):
        """Get Knowledge Base ID"""
        return self.knowledge_base["knowledgeBaseId"]

    def get_bucket_name(self):
        """Get the S3 bucket name"""
        return self.s3_bucket_name

    def cleanup_resources(self, remove_from_parameter_store=True):
        """Clean up Knowledge Base resources (simplified)"""
        try:
            # Delete data source
            if hasattr(self, 'data_source') and self.data_source:
                self.bedrock_agent_client.delete_data_source(
                    dataSourceId=self.data_source["dataSourceId"],
                    knowledgeBaseId=self.knowledge_base['knowledgeBaseId']
                )
                print("Deleted data source")

            # Delete knowledge base
            if hasattr(self, 'knowledge_base') and self.knowledge_base:
                self.bedrock_agent_client.delete_knowledge_base(
                    knowledgeBaseId=self.knowledge_base['knowledgeBaseId']
                )
                print("Deleted knowledge base")

            # Delete OpenSearch collection
            if hasattr(self, 'collection_id') and self.collection_id:
                self.aoss_client.delete_collection(id=self.collection_id)
                print("Deleted OpenSearch collection")

            # Remove from Parameter Store
            if remove_from_parameter_store:
                try:
                    self.ssm_client.delete_parameter(Name=self.parameter_name)
                    print(f"Removed Knowledge Base ID from Parameter Store: {self.parameter_name}")
                except self.ssm_client.exceptions.ParameterNotFound:
                    print("Parameter not found in Parameter Store (already removed)")
                except Exception as e:
                    print(f"Error removing parameter from Parameter Store: {e}")

            print("Cleanup completed")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")