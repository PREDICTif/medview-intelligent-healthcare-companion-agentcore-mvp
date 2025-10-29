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
current_time = time.time()
timestamp_str = time.strftime("%Y%m%d%H%M%S", time.localtime(current_time))[-7:]
suffix = f"{timestamp_str}"

knowledge_base_name = f"diabetes-agent-kb-{suffix}"
knowledge_base_description = "Diabetes Agent Knowledge Base for medical information"
s3_bucket_name = 'mihc-diabetes-kb'

# Create Knowledge Base
print("Creating Knowledge Base...")
knowledge_base = BedrockKnowledgeBase(
    kb_name=knowledge_base_name,
    kb_description=knowledge_base_description,
    s3_bucket_name=s3_bucket_name,
    chunking_strategy="FIXED_SIZE",
    suffix=suffix
)

# Wait for resources to be ready
print("Waiting for resources to be ready...")
time.sleep(60)

# Start data ingestion
print("Starting data ingestion...")
knowledge_base.start_ingestion_job()

# Get Knowledge Base ID
kb_id = knowledge_base.get_knowledge_base_id()
print(f"Knowledge Base created successfully!")
print(f"Knowledge Base ID: {kb_id}")
print(f"S3 Bucket: {s3_bucket_name}")

# Demonstrate Parameter Store functionality
print("\n" + "="*50)
print("Parameter Store Integration:")
print("="*50)

# The KB ID is automatically saved during creation, but let's verify
saved_kb_id = knowledge_base.get_kb_id_from_parameter_store()
if saved_kb_id == kb_id:
    print("✓ Knowledge Base ID successfully saved to Parameter Store")
else:
    print("✗ Issue with Parameter Store save/retrieve")

# Show how to retrieve KB ID by name (useful for other scripts)
retrieved_kb_id = BedrockKnowledgeBase.get_kb_id_by_name(knowledge_base_name)
print(f"Retrieved KB ID by name: {retrieved_kb_id}")

# List all saved Knowledge Bases
print("\nAll saved Knowledge Bases:")
knowledge_base.list_saved_knowledge_bases()
