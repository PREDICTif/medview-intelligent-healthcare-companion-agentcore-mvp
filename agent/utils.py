#!/usr/bin/env python3
"""
Utility functions for the medical assistant agent
"""

import os
import boto3
from botocore.exceptions import ClientError


def get_aws_region():
    """Get AWS region from environment or default to us-east-1"""
    return os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')


def get_ssm_parameter(parameter_name: str, region: str = None) -> str:
    """
    Get parameter value from AWS Systems Manager Parameter Store
    
    Args:
        parameter_name: Name of the SSM parameter
        region: AWS region (optional, uses default if not provided)
        
    Returns:
        Parameter value as string
        
    Raises:
        ClientError: If parameter not found or access denied
    """
    if region is None:
        region = get_aws_region()
    
    ssm = boto3.client('ssm', region_name=region)
    
    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ParameterNotFound':
            raise ClientError(
                error_response={'Error': {'Code': 'ParameterNotFound', 'Message': f'Parameter {parameter_name} not found'}},
                operation_name='GetParameter'
            )
        else:
            raise


def query_knowledge_base(query: str, kb_id: str, region: str = None, max_results: int = 5) -> dict:
    """
    Query Bedrock Knowledge Base for relevant information
    
    Args:
        query: Search query string
        kb_id: Knowledge Base ID
        region: AWS region (optional)
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary containing search results
    """
    if region is None:
        region = get_aws_region()
    
    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=region)
    
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        )
        
        return {
            'results': response.get('retrievalResults', []),
            'query': query,
            'kb_id': kb_id
        }
        
    except ClientError as e:
        print(f"Error querying knowledge base: {e}")
        return {
            'results': [],
            'query': query,
            'kb_id': kb_id,
            'error': str(e)
        }


def check_chunks_relevance(query: str, chunks: list, threshold: float = 0.5) -> list:
    """
    Check relevance of knowledge base chunks to the query
    
    Args:
        query: Original search query
        chunks: List of retrieved chunks
        threshold: Relevance threshold (0.0 to 1.0)
        
    Returns:
        List of relevant chunks above threshold
    """
    relevant_chunks = []
    
    for chunk in chunks:
        # Get confidence score from chunk metadata
        confidence = chunk.get('score', 0.0)
        
        if confidence >= threshold:
            relevant_chunks.append({
                'content': chunk.get('content', {}).get('text', ''),
                'score': confidence,
                'metadata': chunk.get('metadata', {}),
                'location': chunk.get('location', {})
            })
    
    # Sort by relevance score (highest first)
    relevant_chunks.sort(key=lambda x: x['score'], reverse=True)
    
    return relevant_chunks


def format_knowledge_base_results(results: list, max_length: int = 2000) -> str:
    """
    Format knowledge base results for inclusion in agent response
    
    Args:
        results: List of knowledge base results
        max_length: Maximum length of formatted text
        
    Returns:
        Formatted string containing relevant information
    """
    if not results:
        return "No relevant information found in knowledge base."
    
    formatted_text = "Knowledge Base Information:\n\n"
    current_length = len(formatted_text)
    
    for i, result in enumerate(results, 1):
        content = result.get('content', '')
        score = result.get('score', 0.0)
        
        # Add result with score
        result_text = f"{i}. (Relevance: {score:.2f}) {content}\n\n"
        
        # Check if adding this result would exceed max length
        if current_length + len(result_text) > max_length:
            formatted_text += f"... ({len(results) - i + 1} more results truncated)\n"
            break
        
        formatted_text += result_text
        current_length += len(result_text)
    
    return formatted_text.strip()


def check_aws_region() -> dict:
    """
    Check current AWS region and validate it's supported for Bedrock
    
    Returns:
        Dictionary with region info and validation status
    """
    region = get_aws_region()
    
    # List of regions that support Bedrock (as of 2024)
    bedrock_regions = [
        'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
    ]
    
    return {
        'region': region,
        'bedrock_supported': region in bedrock_regions,
        'bedrock_regions': bedrock_regions
    }


def validate_environment() -> dict:
    """
    Validate that required environment variables and AWS services are available
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'aws_region': check_aws_region(),
        'aws_credentials': False,
        'bedrock_access': False,
        'ssm_access': False
    }
    
    try:
        # Test AWS credentials
        sts = boto3.client('sts')
        sts.get_caller_identity()
        validation_results['aws_credentials'] = True
        
        # Test Bedrock access
        bedrock = boto3.client('bedrock-runtime', region_name=get_aws_region())
        # Note: This is a minimal test - actual model access would require more specific testing
        validation_results['bedrock_access'] = True
        
        # Test SSM access
        ssm = boto3.client('ssm', region_name=get_aws_region())
        # Try to list parameters (minimal permission test)
        ssm.describe_parameters(MaxResults=1)
        validation_results['ssm_access'] = True
        
    except Exception as e:
        print(f"Environment validation error: {e}")
    
    return validation_results