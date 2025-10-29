import warnings
# Suppress all deprecation warnings at the start
warnings.filterwarnings("ignore", category=DeprecationWarning)

import boto3
import json
import os
import asyncio, re
from strands import Agent, tool
# Try different import locations for Document class (LangChain versions vary)
try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:
        try:
            from langchain.docstore.document import Document
        except ImportError:
            from langchain_community.docstore.document import Document
from strands_tools import agent_graph, retrieve
from langchain_aws import ChatBedrockConverse, BedrockEmbeddings
from ragas import SingleTurnSample
from ragas.metrics import LLMContextPrecisionWithoutReference
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_tavily import TavilySearch

eval_modelId = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
thinking_params= {
    "thinking": {
        "type": "disabled"
    }
}
llm_for_evaluation = ChatBedrockConverse(model_id=eval_modelId, additional_model_request_fields=thinking_params)
llm_for_evaluation = LangchainLLMWrapper(llm_for_evaluation)

# Use Bedrock embeddings with the wrapper (deprecated but still functional)
bedrock_embeddings_client = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
bedrock_embeddings = LangchainEmbeddingsWrapper(bedrock_embeddings_client)

# Load environment variables
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get TAVILY_API_KEY from environment
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables. Please check your .env file.")

# Initialize Tavily search tool with the modern API
web_search_tool = TavilySearch(api_key=TAVILY_API_KEY, max_results=3)

@tool
def check_chunks_relevance(results: str, question: str):
    """
    Evaluates the relevance of retrieved chunks to the user question using RAGAs.

    Args:
        results (str): Retrieval output as a string with 'Score:' and 'Content:' patterns.
        question (str): Original user question.

    Returns:
        dict: A binary score ('yes' or 'no') and the numeric relevance score, or an error message.
    """
    try:
        if not results or not isinstance(results, str):
            raise ValueError("Invalid input: 'results' must be a non-empty string.")
        if not question or not isinstance(question, str):
            raise ValueError("Invalid input: 'question' must be a non-empty string.")

        # Extract content chunks using regex
        pattern = r"Score:.*?\nContent:\s*(.*?)(?=Score:|\Z)"
        docs = [chunk.strip() for chunk in re.findall(pattern, results, re.DOTALL)]

        if not docs:
            raise ValueError("No valid content chunks found in 'results'.")

        # Prepare evaluation sample
        sample = SingleTurnSample(
            user_input=question,
            response="placeholder-response",  # required dummy response
            retrieved_contexts=docs
        )

        # Evaluate using context precision metric
        scorer = LLMContextPrecisionWithoutReference(llm=llm_for_evaluation)
        score = asyncio.run(scorer.single_turn_ascore(sample))

        print("------------------------")
        print("Context evaluation")
        print("------------------------")
        print(f"chunk_relevance_score: {score}")

        return {
            "chunk_relevance_score": "yes" if score > 0.5 else "no",
            "chunk_relevance_value": score
        }

    except Exception as e:
        return {
            "error": str(e),
            "chunk_relevance_score": "unknown",
            "chunk_relevance_value": None
        }

@tool
def query_knowledge_base(query: str, kb_name: str = "diabetes-agent-kb"):
    """
    Query the medical knowledge base for diabetes-related information.
    
    Args:
        query (str): The medical question to search for
        kb_name (str): Name of the knowledge base (defaults to diabetes KB)
    
    Returns:
        str: Formatted results from the knowledge base with scores and content
    """
    try:
        print(f"---KNOWLEDGE BASE QUERY---")
        print(f"Query: {query}")
        print(f"KB Name: {kb_name}")
        
        # Get KB ID from Parameter Store
        ssm_client = boto3.client('ssm')
        parameter_name = f"/bedrock/knowledge-base/{kb_name}/kb-id"
        
        try:
            response = ssm_client.get_parameter(Name=parameter_name)
            kb_id = response['Parameter']['Value']
            print(f"Found KB ID: {kb_id}")
        except ssm_client.exceptions.ParameterNotFound:
            # Try to find any diabetes-related KB
            try:
                response = ssm_client.get_parameters_by_path(
                    Path="/bedrock/knowledge-base/",
                    Recursive=True
                )
                
                diabetes_kbs = []
                for param in response['Parameters']:
                    if 'diabetes' in param['Name'].lower():
                        kb_name_from_param = param['Name'].split('/')[-2]
                        diabetes_kbs.append({
                            'name': kb_name_from_param,
                            'kb_id': param['Value']
                        })
                
                if diabetes_kbs:
                    kb_id = diabetes_kbs[0]['kb_id']
                    actual_kb_name = diabetes_kbs[0]['name']
                    print(f"Using diabetes KB: {actual_kb_name} (ID: {kb_id})")
                else:
                    return f"Error: No knowledge base found with name '{kb_name}' or diabetes-related KBs in Parameter Store"
                    
            except Exception as e:
                return f"Error accessing Parameter Store: {str(e)}"
        
        # Query the Knowledge Base
        bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {'numberOfResults': 5}
            }
        )
        
        results = response['retrievalResults']
        
        if not results:
            return f"No results found in knowledge base for query: {query}"
        
        # Format results for the agent
        formatted_results = f"Knowledge Base Results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            score = result['score']
            content = result['content']['text']
            source = ""
            
            if 'location' in result and 's3Location' in result['location']:
                source = f"\nSource: {result['location']['s3Location']['uri']}"
            
            formatted_results += f"Result {i}:\nScore: {score:.4f}\nContent: {content}{source}\n\n"
        
        print(f"Retrieved {len(results)} results from knowledge base")
        return formatted_results
        
    except Exception as e:
        error_msg = f"Error querying knowledge base: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def web_search(query):
    """
    Perform web search based on the query and return results as Documents.
    Only to be used if chunk_relevance_score is no.

    Args:
        query (str): The user question or rephrased query.

    Returns:
        dict: {
            "documents": [Document, ...]  # list of Document objects with web results
        }
    """

    print("---WEB SEARCH---")

    # Perform web search
    docs = web_search_tool.invoke({"query": query})

    # Convert each result into a Document object
    documents = [Document(page_content=d["content"]) for d in docs]

    return {
        "documents": documents
    }
