# Simplified Bedrock Knowledge Base with Parameter Store Integration

This simplified Knowledge Base implementation focuses on creating and managing Bedrock Knowledge Bases with S3 data sources, enhanced with AWS Systems Manager Parameter Store integration for persistent storage of Knowledge Base IDs.

## Project Structure

### Core Files

#### Production Code
- **`utils/knowledge_base.py`** - Main simplified Knowledge Base class
- **`create_kb.py`** - Script to create Knowledge Base with Parameter Store integration
- **`requirements.txt`** - Python dependencies



#### Configuration
- **`.env`** - Environment variables (if needed)

## Key Features

✅ **Simplified Knowledge Base Creation**
- S3 data source only
- OpenSearch Serverless vector store
- Automatic IAM role and policy creation

✅ **Parameter Store Integration**
- Automatic KB ID persistence
- Easy retrieval by name
- Proper tag management

✅ **Production Ready**
- Comprehensive error handling
- Retry logic for timing issues
- Clean, maintainable code

✅ **User Friendly**
- Clear progress indicators
- Helpful error messages
- Simple API interface

## Parameter Store Integration

### Automatic Storage
When a Knowledge Base is created, its ID is automatically saved to AWS Systems Manager Parameter Store at:
```
/bedrock/knowledge-base/{kb_name}/kb-id
```

### Benefits
- **Persistence**: KB IDs survive across sessions and deployments
- **Easy Retrieval**: Access KB IDs from any script or application
- **Centralized Management**: All KB IDs stored in one location
- **Metadata**: Parameters include tags with KB name, S3 bucket, and creation info

## Usage Examples

### 1. Create Knowledge Base (saves ID automatically)
```python
from utils.knowledge_base import BedrockKnowledgeBase

kb = BedrockKnowledgeBase(
    kb_name="diabetes-agent-kb",
    kb_description="Medical information KB",
    s3_bucket_name="mihc-diabetes-kb"
)

# KB ID is automatically saved to Parameter Store
kb_id = kb.get_knowledge_base_id()
```

### 2. Retrieve KB ID by Name
```python
# From anywhere in your code
kb_id = BedrockKnowledgeBase.get_kb_id_by_name("diabetes-agent-kb")
```

### 3. List All Saved Knowledge Bases
```python
# Create temporary instance to access class methods
temp_kb = BedrockKnowledgeBase("temp", "temp", "temp")
saved_kbs = temp_kb.list_saved_knowledge_bases()

# Or use direct Parameter Store access
import boto3
ssm = boto3.client('ssm')
response = ssm.get_parameters_by_path(Path="/bedrock/knowledge-base/", Recursive=True)
for param in response['Parameters']:
    kb_name = param['Name'].split('/')[-2]
    kb_id = param['Value']
    print(f"{kb_name}: {kb_id}")
```

## Quick Start

### Create Knowledge Base
```bash
python create_kb.py
```

### Use the Knowledge Base
Once created, you can use the Knowledge Base programmatically:

```python
from utils.knowledge_base import BedrockKnowledgeBase
import boto3

# Retrieve KB ID from Parameter Store
kb_id = BedrockKnowledgeBase.get_kb_id_by_name("diabetes-agent-kb-1234567")

# Query the Knowledge Base
bedrock_runtime = boto3.client('bedrock-agent-runtime')
response = bedrock_runtime.retrieve(
    knowledgeBaseId=kb_id,
    retrievalQuery={'text': "What is diabetes?"},
    retrievalConfiguration={
        'vectorSearchConfiguration': {'numberOfResults': 5}
    }
)

# Process results
for result in response['retrievalResults']:
    print(f"Score: {result['score']:.4f}")
    print(f"Content: {result['content']['text'][:200]}...")
    print()
```

## Core Components

### `create_kb.py`
Main script that creates a new Knowledge Base with Parameter Store integration. The KB ID is automatically saved for later retrieval.

### `utils/knowledge_base.py`
The main Knowledge Base class containing all functionality:
- Knowledge Base creation and management
- Parameter Store integration
- S3 data source configuration
- OpenSearch Serverless setup
- IAM role and policy management



## Parameter Store Structure

Parameters are stored with the following structure:
```
/bedrock/knowledge-base/
├── diabetes-agent-kb-1234567/
│   └── kb-id (value: actual-kb-id-here)
├── medical-kb-7654321/
│   └── kb-id (value: another-kb-id-here)
└── ...
```

Each parameter includes tags:
- `KnowledgeBaseName`: The friendly name of the KB
- `S3Bucket`: The associated S3 bucket
- `CreatedBy`: Set to "BedrockKnowledgeBase"

## API Methods

### Parameter Store Methods

#### `save_kb_id_to_parameter_store(kb_id)`
Saves a Knowledge Base ID to Parameter Store (called automatically during creation).

#### `get_kb_id_from_parameter_store()`
Retrieves the KB ID for this instance from Parameter Store.

#### `get_kb_id_by_name(kb_name, region_name=None)` (Class Method)
Retrieves any KB ID by name from Parameter Store.

#### `list_saved_knowledge_bases()`
Lists all saved Knowledge Base IDs from Parameter Store.

### Core Methods

#### `create_knowledge_base()`
Creates the Knowledge Base and automatically saves ID to Parameter Store.

#### `start_ingestion_job()`
Starts data ingestion from S3 to the Knowledge Base.

#### `cleanup_resources(remove_from_parameter_store=True)`
Cleans up all resources, optionally removing from Parameter Store.

## Configuration

The Knowledge Base uses these AWS services:
- **Bedrock**: For the Knowledge Base and embedding models
- **OpenSearch Serverless**: For vector storage
- **S3**: For source data storage
- **IAM**: For permissions and roles
- **Systems Manager Parameter Store**: For KB ID persistence

## Requirements

```
boto3
opensearch-py
```

## IAM Permissions

Your AWS credentials need permissions for:
- Bedrock (Knowledge Base operations)
- OpenSearch Serverless
- IAM (role and policy creation)
- S3 (bucket access)
- **Systems Manager (Parameter Store operations)**

## Error Handling

The implementation includes comprehensive error handling for:
- Resource conflicts (existing resources are reused)
- Parameter Store operations (graceful handling of missing parameters)
- Network timeouts and retries
- Resource cleanup failures

## Best Practices

1. **Naming**: Use descriptive, unique names for Knowledge Bases
2. **Cleanup**: Always clean up test resources to avoid costs
3. **Monitoring**: Check Parameter Store for orphaned parameters
4. **Security**: Ensure proper IAM permissions for Parameter Store access

## Clean, Production-Ready Codebase

The Knowledge Base implementation is now:
- **Focused** - Only essential functionality
- **Clean** - No debug or test code
- **Documented** - Clear documentation with examples
- **Reliable** - Proper error handling and retry logic
- **Maintainable** - Simple, well-structured code

### Removed Files
All test, debug, and troubleshooting files have been cleaned up:
- ❌ `test_*.py` files
- ❌ `troubleshoot_*.py` files  
- ❌ `fix_*.md` debug documentation
- ❌ Debug methods from main code
- ❌ Temporary documentation files

## Troubleshooting

### Common Issues and Solutions

#### 1. ValidationException with 403 Forbidden
This usually indicates OpenSearch Serverless access policy issues:

**Solution:**
Check your AWS IAM permissions and ensure proper access policies are configured.

**Common causes:**
- Access policies need time to propagate (wait 60+ seconds)
- IAM role not included in OpenSearch access policy
- Collection not in ACTIVE status
- Timing issues between resource creation

#### 2. Parameter Store Issues

**ValidationException with tags and overwrite:**
Fixed in the implementation - now handles new vs existing parameters correctly.

**Common solutions:**
- Ensure IAM permissions include `ssm:GetParameter`, `ssm:PutParameter`, `ssm:DeleteParameter`, `ssm:AddTagsToResource`, `ssm:RemoveTagsFromResource`
- Check parameter names match the expected format: `/bedrock/knowledge-base/{kb_name}/kb-id`
- Verify region consistency between resources and Parameter Store

#### 3. Knowledge Base Creation Issues
- Verify S3 bucket exists and is accessible
- Check IAM role permissions for Bedrock, S3, and OpenSearch
- Ensure OpenSearch Serverless quotas are not exceeded
- Wait for IAM roles and policies to propagate

#### 4. Timing Issues
The implementation includes automatic waits, but you may need longer delays:
- IAM role propagation: 30-60 seconds
- OpenSearch collection activation: 2-5 minutes  
- Access policy propagation: 60+ seconds



### Required IAM Permissions

Your AWS credentials need these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*",
                "aoss:*",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:CreatePolicy",
                "iam:GetRole",
                "iam:ListAttachedRolePolicies",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:HeadBucket",
                "ssm:GetParameter",
                "ssm:PutParameter", 
                "ssm:DeleteParameter",
                "ssm:DescribeParameters",
                "ssm:GetParametersByPath",
                "ssm:AddTagsToResource",
                "ssm:RemoveTagsFromResource",
                "ssm:ListTagsForResource"
            ],
            "Resource": "*"
        }
    ]
}
```