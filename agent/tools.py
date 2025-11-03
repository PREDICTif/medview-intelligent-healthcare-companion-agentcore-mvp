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
# Heavy imports commented out to reduce Lambda deployment complexity
# from strands_tools import agent_graph, retrieve
# from langchain_aws import ChatBedrockConverse, BedrockEmbeddings
# from ragas import SingleTurnSample
# from ragas.metrics import LLMContextPrecisionWithoutReference
# from ragas.llms import LangchainLLMWrapper
# from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_tavily import TavilySearch

# RAGAS evaluation setup (commented out)
# eval_modelId = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
# thinking_params= {
#     "thinking": {
#         "type": "disabled"
#     }
# }
# llm_for_evaluation = ChatBedrockConverse(model_id=eval_modelId, additional_model_request_fields=thinking_params)
# llm_for_evaluation = LangchainLLMWrapper(llm_for_evaluation)

# Use Bedrock embeddings with the wrapper (commented out)
# bedrock_embeddings_client = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
# bedrock_embeddings = LangchainEmbeddingsWrapper(bedrock_embeddings_client)

# Load environment variables (try .env file for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in production, that's fine
    pass

# Get TAVILY_API_KEY from environment
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# Initialize Tavily search tool with the modern API (only if API key is available)
web_search_tool = None
if TAVILY_API_KEY:
    try:
        web_search_tool = TavilySearch(api_key=TAVILY_API_KEY, max_results=3)
        print("✅ Tavily search tool initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize Tavily search tool: {e}")
        web_search_tool = None
else:
    print("⚠️ Warning: TAVILY_API_KEY not found. Web search will not be available.")

def _query_knowledge_base_internal(query: str, kb_name: str = "diabetes-agent-kb"):
    """
    Internal helper function to query the medical knowledge base.
    
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
        
        # Get current region from session or environment
        session = boto3.Session()
        region_name = session.region_name or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        print(f"Using AWS region: {region_name}")
        
        # Get KB ID from Parameter Store
        ssm_client = boto3.client('ssm', region_name=region_name)
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
        
        # Query the Knowledge Base with explicit region and configuration
        bedrock_runtime = boto3.client(
            'bedrock-agent-runtime', 
            region_name=region_name,
            config=boto3.session.Config(
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                read_timeout=60,
                connect_timeout=60
            )
        )
        
        print(f"Bedrock client endpoint: {bedrock_runtime._endpoint.host}")
        print(f"Attempting to retrieve from KB ID: {kb_id}")
        
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

# @tool
# def check_chunks_relevance(results: str, question: str):
#     """
#     Evaluates the relevance of retrieved chunks to the user question using RAGAs.
#     COMMENTED OUT: This tool uses asyncio and RAGAS which can cause Lambda deployment issues.
#     
#     Args:
#         results (str): Retrieval output as a string with 'Score:' and 'Content:' patterns.
#         question (str): Original user question.
# 
#     Returns:
#         dict: A binary score ('yes' or 'no') and the numeric relevance score, or an error message.
#     """
#     try:
#         if not results or not isinstance(results, str):
#             raise ValueError("Invalid input: 'results' must be a non-empty string.")
#         if not question or not isinstance(question, str):
#             raise ValueError("Invalid input: 'question' must be a non-empty string.")
# 
#         # Extract content chunks using regex
#         pattern = r"Score:.*?\nContent:\s*(.*?)(?=Score:|\Z)"
#         docs = [chunk.strip() for chunk in re.findall(pattern, results, re.DOTALL)]
# 
#         if not docs:
#             raise ValueError("No valid content chunks found in 'results'.")
# 
#         # Prepare evaluation sample
#         sample = SingleTurnSample(
#             user_input=question,
#             response="placeholder-response",  # required dummy response
#             retrieved_contexts=docs
#         )
# 
#         # Evaluate using context precision metric
#         scorer = LLMContextPrecisionWithoutReference(llm=llm_for_evaluation)
#         
#         # Handle asyncio in Lambda environment
#         try:
#             # Try to get existing event loop
#             loop = asyncio.get_event_loop()
#             if loop.is_running():
#                 # If loop is already running (like in Lambda), create a task
#                 import concurrent.futures
#                 with concurrent.futures.ThreadPoolExecutor() as executor:
#                     future = executor.submit(asyncio.run, scorer.single_turn_ascore(sample))
#                     score = future.result()
#             else:
#                 score = asyncio.run(scorer.single_turn_ascore(sample))
#         except RuntimeError:
#             # Fallback for Lambda environment
#             score = asyncio.run(scorer.single_turn_ascore(sample))
# 
#         print("------------------------")
#         print("Context evaluation")
#         print("------------------------")
#         print(f"chunk_relevance_score: {score}")
# 
#         return {
#             "chunk_relevance_score": "yes" if score > 0.5 else "no",
#             "chunk_relevance_value": score
#         }
# 
#     except Exception as e:
#         return {
#             "error": str(e),
#             "chunk_relevance_score": "unknown",
#             "chunk_relevance_value": None
#         }





@tool
def diabetes_specialist_tool(patient_query: str, patient_context: str = ""):
    """
    Specialized diabetes consultation tool that provides comprehensive diabetes-related guidance.
    
    This tool combines knowledge base search with specialized diabetes expertise to provide:
    - Symptom analysis and risk assessment
    - Treatment options and medication guidance
    - Lifestyle and dietary recommendations
    - Blood sugar management strategies
    - Complication prevention advice
    
    Args:
        patient_query (str): The patient's question or concern about diabetes
        patient_context (str): Optional context about the patient (age, type of diabetes, current medications, etc.)
    
    Returns:
        str: Comprehensive diabetes consultation response with evidence-based recommendations
    """
    try:
        print(f"---DIABETES SPECIALIST CONSULTATION---")
        print(f"Patient Query: {patient_query}")
        print(f"Patient Context: {patient_context}")
        
        # Enhanced query for knowledge base search
        enhanced_query = f"diabetes {patient_query}"
        if patient_context:
            enhanced_query += f" {patient_context}"
        
        # Query the knowledge base first
        kb_results = _query_knowledge_base_internal(enhanced_query, "diabetes-agent-kb")
        
        # Analyze the query type to provide specialized guidance
        query_lower = patient_query.lower()
        consultation_type = "general"
        
        if any(word in query_lower for word in ["symptom", "sign", "feel", "experience"]):
            consultation_type = "symptoms"
        elif any(word in query_lower for word in ["treatment", "medication", "medicine", "drug"]):
            consultation_type = "treatment"
        elif any(word in query_lower for word in ["diet", "food", "eat", "nutrition", "meal"]):
            consultation_type = "nutrition"
        elif any(word in query_lower for word in ["blood sugar", "glucose", "a1c", "monitor"]):
            consultation_type = "monitoring"
        elif any(word in query_lower for word in ["complication", "risk", "prevent"]):
            consultation_type = "complications"
        
        # Create specialized response based on consultation type
        specialist_guidance = {
            "symptoms": """
🔍 SYMPTOM ANALYSIS FRAMEWORK:
- Document frequency, severity, and timing
- Consider blood glucose patterns
- Assess for emergency signs (DKA, severe hypoglycemia)
- Evaluate for complications (neuropathy, retinopathy, nephropathy)
""",
            "treatment": """
💊 TREATMENT CONSIDERATIONS:
- Current medications and dosing
- A1C targets and individualization
- Side effect profiles and contraindications
- Lifestyle modifications as first-line therapy
- Regular monitoring requirements
""",
            "nutrition": """
🥗 NUTRITIONAL GUIDANCE:
- Carbohydrate counting and glycemic index
- Portion control and meal timing
- Balanced macronutrient distribution
- Special considerations for type 1 vs type 2
- Integration with medication timing
""",
            "monitoring": """
📊 MONITORING STRATEGIES:
- Blood glucose testing frequency and timing
- A1C targets (typically <7% for most adults)
- Continuous glucose monitoring benefits
- Ketone testing when indicated
- Regular screening for complications
""",
            "complications": """
⚠️ COMPLICATION PREVENTION:
- Annual eye exams for retinopathy
- Kidney function monitoring (eGFR, microalbumin)
- Foot care and neuropathy screening
- Cardiovascular risk assessment
- Blood pressure and lipid management
""",
            "general": """
🏥 COMPREHENSIVE DIABETES CARE:
- Multidisciplinary team approach
- Patient education and self-management
- Regular follow-up scheduling
- Emergency action plans
- Quality of life considerations
"""
        }
        
        # Format the comprehensive response
        response = f"""
DIABETES SPECIALIST CONSULTATION
================================

Patient Query: {patient_query}
{f"Patient Context: {patient_context}" if patient_context else ""}

{specialist_guidance.get(consultation_type, specialist_guidance["general"])}

EVIDENCE-BASED INFORMATION FROM KNOWLEDGE BASE:
{kb_results}

CLINICAL RECOMMENDATIONS:
• Always consult with healthcare providers for personalized medical advice
• Monitor blood glucose as recommended by your care team
• Maintain regular follow-up appointments
• Report any concerning symptoms promptly
• Consider diabetes self-management education programs

⚠️ IMPORTANT DISCLAIMER:
This information is for educational purposes only and does not replace professional medical advice. 
Always consult with qualified healthcare providers for diagnosis and treatment decisions.
"""
        
        print(f"Generated specialized diabetes consultation response")
        return response
        
    except Exception as e:
        error_msg = f"Error in diabetes specialist consultation: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def amd_specialist_tool(patient_query: str, patient_context: str = ""):
    """
    Specialized Age-related Macular Degeneration (AMD) consultation tool that provides comprehensive AMD-related guidance.
    
    This tool combines knowledge base search with specialized AMD expertise to provide:
    - Early detection and risk assessment
    - Dry vs wet AMD differentiation
    - Treatment options and management strategies
    - Vision preservation techniques
    - Lifestyle modifications and supplements
    - Monitoring and follow-up recommendations
    
    Args:
        patient_query (str): The patient's question or concern about AMD or vision problems
        patient_context (str): Optional context about the patient (age, family history, current vision status, etc.)
    
    Returns:
        str: Comprehensive AMD consultation response with evidence-based recommendations
    """
    try:
        print(f"---AMD SPECIALIST CONSULTATION---")
        print(f"Patient Query: {patient_query}")
        print(f"Patient Context: {patient_context}")
        
        # Enhanced query for knowledge base search
        enhanced_query = f"age-related macular degeneration AMD {patient_query}"
        if patient_context:
            enhanced_query += f" {patient_context}"
        
        # Query the knowledge base first
        kb_results = _query_knowledge_base_internal(enhanced_query, "diabetes-agent-kb")
        
        # Analyze the query type to provide specialized guidance
        query_lower = patient_query.lower()
        consultation_type = "general"
        
        if any(word in query_lower for word in ["symptom", "sign", "vision", "see", "sight", "blur"]):
            consultation_type = "symptoms"
        elif any(word in query_lower for word in ["treatment", "injection", "anti-vegf", "lucentis", "eylea", "avastin"]):
            consultation_type = "treatment"
        elif any(word in query_lower for word in ["diet", "supplement", "vitamin", "nutrition", "areds"]):
            consultation_type = "nutrition"
        elif any(word in query_lower for word in ["monitor", "test", "exam", "amsler", "oct"]):
            consultation_type = "monitoring"
        elif any(word in query_lower for word in ["prevent", "risk", "family history", "genetics"]):
            consultation_type = "prevention"
        elif any(word in query_lower for word in ["dry", "wet", "type", "stage", "advanced"]):
            consultation_type = "classification"
        
        # Create specialized response based on consultation type
        specialist_guidance = {
            "symptoms": """
👁️ AMD SYMPTOM ASSESSMENT FRAMEWORK:
- Central vision changes (straight lines appear wavy)
- Dark or empty spots in central vision
- Difficulty reading or recognizing faces
- Need for brighter light when reading
- Decreased intensity or brightness of colors
- Amsler grid testing for metamorphopsia
""",
            "treatment": """
💉 AMD TREATMENT OPTIONS:
- Anti-VEGF injections for wet AMD (ranibizumab, aflibercept, bevacizumab)
- Photodynamic therapy in select cases
- Thermal laser photocoagulation (rarely used)
- Low vision rehabilitation and aids
- No proven treatment for dry AMD (except advanced cases)
- Clinical trials for emerging therapies
""",
            "nutrition": """
🥬 NUTRITIONAL INTERVENTIONS:
- AREDS2 formula supplements (zinc, vitamins C & E, lutein, zeaxanthin)
- Dark leafy greens (spinach, kale, collard greens)
- Omega-3 fatty acids from fish
- Avoid high-dose beta-carotene (especially smokers)
- Mediterranean diet pattern
- Limit processed foods and refined sugars
""",
            "monitoring": """
📊 AMD MONITORING STRATEGIES:
- Regular dilated eye exams (annually or as recommended)
- Amsler grid testing at home (daily for high-risk patients)
- Optical Coherence Tomography (OCT) imaging
- Fluorescein angiography for wet AMD evaluation
- Visual acuity testing
- Immediate evaluation for sudden vision changes
""",
            "prevention": """
⚠️ AMD RISK REDUCTION:
- Smoking cessation (most important modifiable risk factor)
- UV protection with quality sunglasses
- Regular exercise and cardiovascular health
- Blood pressure and cholesterol management
- Healthy diet rich in antioxidants
- Family history awareness and genetic counseling
""",
            "classification": """
🔍 AMD CLASSIFICATION & STAGING:
- Early AMD: Few medium drusen, no vision loss
- Intermediate AMD: Many medium drusen or large drusen
- Advanced dry AMD: Geographic atrophy in central retina
- Advanced wet AMD: Choroidal neovascularization
- Wet AMD requires urgent ophthalmologic evaluation
- Dry AMD progression monitoring essential
""",
            "general": """
👁️ COMPREHENSIVE AMD CARE:
- Multidisciplinary approach with retinal specialists
- Patient education on disease progression
- Low vision rehabilitation services
- Support groups and counseling
- Adaptive technology and devices
- Regular monitoring and early intervention
"""
        }
        
        # Format the comprehensive response
        response = f"""
AMD SPECIALIST CONSULTATION
===========================

Patient Query: {patient_query}
{f"Patient Context: {patient_context}" if patient_context else ""}

{specialist_guidance.get(consultation_type, specialist_guidance["general"])}

EVIDENCE-BASED INFORMATION FROM KNOWLEDGE BASE:
{kb_results}

CLINICAL RECOMMENDATIONS:
• Immediate ophthalmologic evaluation for sudden vision changes
• Regular monitoring with Amsler grid testing
• AREDS2 supplements for intermediate AMD or advanced AMD in one eye
• Smoking cessation counseling if applicable
• UV protection and cardiovascular risk management
• Low vision rehabilitation referral when appropriate

⚠️ URGENT REFERRAL INDICATORS:
- Sudden onset of visual distortion or central vision loss
- New onset of metamorphopsia (wavy lines)
- Rapid progression of symptoms
- Suspected conversion from dry to wet AMD

⚠️ IMPORTANT DISCLAIMER:
This information is for educational purposes only and does not replace professional medical advice. 
AMD requires specialized ophthalmologic care. Always consult with qualified eye care professionals for diagnosis and treatment decisions.
"""
        
        print(f"Generated specialized AMD consultation response")
        return response
        
    except Exception as e:
        error_msg = f"Error in AMD specialist consultation: {str(e)}"
        print(error_msg)
        return error_msg

@tool
def web_search(query):
    """
    Perform web search based on the query and return results.

    Args:
        query (str): The user question or search query.

    Returns:
        str: Formatted web search results or error message
    """

    print("---WEB SEARCH---")
    print(f"Query: {query}")

    # Check if web search tool is available
    if web_search_tool is None:
        error_msg = "Web search is not available. TAVILY_API_KEY not configured in environment variables."
        print(f"❌ {error_msg}")
        return error_msg

    try:
        # Perform web search
        docs = web_search_tool.invoke({"query": query})
        
        print(f"Raw web search response: {docs}")
        print(f"Type of docs: {type(docs)}")
        
        if not docs:
            return f"No web search results found for query: {query}"

        # Format results for the agent
        formatted_results = f"Web Search Results for: {query}\n\n"
        
        for i, doc in enumerate(docs, 1):
            print(f"Processing doc {i}: {doc}")
            print(f"Doc type: {type(doc)}")
            
            content = doc.get("content", "No content available")
            url = doc.get("url", "No URL available")
            title = doc.get("title", "No title available")
            
            formatted_results += f"Result {i}:\nTitle: {title}\nURL: {url}\nContent: {content}\n\n"
        
        print(f"Retrieved {len(docs)} web search results")
        print(f"Final formatted results: {formatted_results}")
        return formatted_results
        
    except Exception as e:
        error_msg = f"Web search failed: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
