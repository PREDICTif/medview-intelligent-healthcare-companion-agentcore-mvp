import time
import boto3
import logging
from utils.knowledge_base import BedrockKnowledgeBase

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
knowledge_base_name = "diabetes-agent-kb"
knowledge_base_description = "Diabetes Agent Knowledge Base for medical information"
s3_bucket_name = 'mihc-diabetes-kb'

# Web scrape URLs for additional data sources
WEB_SCRAPE_URLS = [
    "https://www.cdc.gov/diabetes/basics/index.html",
    "https://www.cdc.gov/diabetes/managing/index.html",
    "https://www.cdc.gov/diabetes/prevention/index.html",
    "https://www.niddk.nih.gov/health-information/diabetes",
    "https://www.mayoclinic.org/diseases-conditions/diabetes/symptoms-causes/syc-20371444",
]


def check_knowledge_base_exists(kb_name: str) -> tuple:
    """
    Check if a knowledge base with the given name already exists.
    
    Returns:
        tuple: (exists: bool, kb_id: str or None, kb_details: dict or None)
    """
    try:
        bedrock_agent = boto3.client('bedrock-agent')
        
        # List all knowledge bases
        response = bedrock_agent.list_knowledge_bases(maxResults=100)
        
        for kb in response.get('knowledgeBaseSummaries', []):
            if kb['name'] == kb_name:
                # Get full details
                kb_id = kb['knowledgeBaseId']
                kb_details = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
                return True, kb_id, kb_details
        
        return False, None, None
        
    except Exception as e:
        logger.error(f"Error checking knowledge base existence: {e}")
        return False, None, None


def add_web_scrape_data_source(kb_id: str, kb_name: str, urls: list) -> str:
    """
    Add a web scrape data source to an existing knowledge base.
    
    Args:
        kb_id: Knowledge base ID
        kb_name: Knowledge base name
        urls: List of URLs to scrape
        
    Returns:
        str: Data source ID
    """
    try:
        bedrock_agent = boto3.client('bedrock-agent')
        
        # Create web crawler data source
        data_source_name = f"{kb_name}-web-scrape"
        
        # Check if data source already exists
        existing_sources = bedrock_agent.list_data_sources(
            knowledgeBaseId=kb_id,
            maxResults=100
        )
        
        for source in existing_sources.get('dataSourceSummaries', []):
            if source['name'] == data_source_name:
                logger.info(f"Web scrape data source already exists: {source['dataSourceId']}")
                return source['dataSourceId']
        
        # Create new web crawler data source
        logger.info(f"Creating web scrape data source with {len(urls)} URLs...")
        
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=data_source_name,
            description="Web scraped medical information from trusted sources",
            dataSourceConfiguration={
                'type': 'WEB',
                'webConfiguration': {
                    'sourceConfiguration': {
                        'urlConfiguration': {
                            'seedUrls': [{'url': url} for url in urls]
                        }
                    },
                    'crawlerConfiguration': {
                        'crawlerLimits': {
                            'rateLimit': 300  # Max pages per minute
                        },
                        'scope': 'HOST_ONLY',  # Only crawl the same host
                        'inclusionFilters': ['*'],
                        'exclusionFilters': []
                    }
                }
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {
                        'maxTokens': 300,
                        'overlapPercentage': 20
                    }
                }
            }
        )
        
        data_source_id = response['dataSource']['dataSourceId']
        logger.info(f"✓ Web scrape data source created: {data_source_id}")
        
        # Start ingestion job for the new data source
        logger.info("Starting ingestion job for web scrape data source...")
        bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        logger.info("✓ Ingestion job started")
        
        return data_source_id
        
    except Exception as e:
        logger.error(f"Error adding web scrape data source: {e}")
        raise


def main():
    """Main function to create or update knowledge base"""
    
    print("="*70)
    print("Knowledge Base Setup")
    print("="*70)
    
    # Check if knowledge base already exists
    print(f"\nChecking if knowledge base '{knowledge_base_name}' exists...")
    exists, kb_id, kb_details = check_knowledge_base_exists(knowledge_base_name)
    
    if exists:
        print(f"✓ Knowledge base already exists!")
        print(f"  Knowledge Base ID: {kb_id}")
        print(f"  Status: {kb_details['knowledgeBase']['status']}")
        print(f"  Created: {kb_details['knowledgeBase']['createdAt']}")
        
        # Ask if user wants to add web scrape data source
        print(f"\nKnowledge base exists. Will add/update web scrape data source...")
        
    else:
        print(f"✗ Knowledge base does not exist. Creating new one...")
        
        # Generate suffix for unique resource names
        current_time = time.time()
        timestamp_str = time.strftime("%Y%m%d%H%M%S", time.localtime(current_time))[-7:]
        suffix = f"{timestamp_str}"
        
        # Create Knowledge Base
        print("\nCreating Knowledge Base...")
        knowledge_base = BedrockKnowledgeBase(
            kb_name=knowledge_base_name,
            kb_description=knowledge_base_description,
            s3_bucket_name=s3_bucket_name,
            chunking_strategy="FIXED_SIZE",
            suffix=suffix
        )
        
        # Wait for resources to be ready
        print("\nWaiting for resources to be ready...")
        time.sleep(60)
        
        # Start data ingestion for S3 data source
        print("\nStarting data ingestion for S3 data source...")
        knowledge_base.start_ingestion_job()
        
        # Get Knowledge Base ID
        kb_id = knowledge_base.get_knowledge_base_id()
        print(f"\n✓ Knowledge Base created successfully!")
        print(f"  Knowledge Base ID: {kb_id}")
        print(f"  S3 Bucket: {s3_bucket_name}")
        
        # Verify Parameter Store save
        saved_kb_id = knowledge_base.get_kb_id_from_parameter_store()
        if saved_kb_id == kb_id:
            print("  ✓ Knowledge Base ID saved to Parameter Store")
        
        # Wait a bit before adding web scrape source
        print("\nWaiting before adding web scrape data source...")
        time.sleep(30)
    
    # Add web scrape data source
    print("\n" + "="*70)
    print("Adding Web Scrape Data Source")
    print("="*70)
    print(f"\nURLs to scrape ({len(WEB_SCRAPE_URLS)}):")
    for i, url in enumerate(WEB_SCRAPE_URLS, 1):
        print(f"  {i}. {url}")
    
    try:
        data_source_id = add_web_scrape_data_source(
            kb_id=kb_id,
            kb_name=knowledge_base_name,
            urls=WEB_SCRAPE_URLS
        )
        print(f"\n✓ Web scrape data source configured: {data_source_id}")
    except Exception as e:
        print(f"\n✗ Failed to add web scrape data source: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("Setup Complete")
    print("="*70)
    print(f"\nKnowledge Base ID: {kb_id}")
    print(f"Knowledge Base Name: {knowledge_base_name}")
    print(f"S3 Bucket: {s3_bucket_name}")
    print(f"Web Scrape URLs: {len(WEB_SCRAPE_URLS)}")
    print("\nData sources:")
    print("  1. S3 bucket (medical documents)")
    print("  2. Web scrape (CDC, NIH, Mayo Clinic)")
    print("\nNote: Ingestion jobs may take several minutes to complete.")
    print("Check status in AWS Console: Bedrock > Knowledge bases")


if __name__ == "__main__":
    main()
