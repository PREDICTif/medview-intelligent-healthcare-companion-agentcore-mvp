"""
Consolidated Tools for Medical Assistant Agent
All agent tools in one place for easier management
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import boto3
import json
import os
import asyncio
import re
import requests
from strands import Agent, tool
from typing import Optional, Dict, Any
from prompts import (
    DIABETES_CONSULTATION_FRAMEWORKS, 
    DIABETES_CLINICAL_RECOMMENDATIONS,
    DIABETES_DISCLAIMER,
    DIABETES_CONSULTATION_TEMPLATE,
    DIABETES_KEYWORDS,
    AMD_CONSULTATION_FRAMEWORKS,
    AMD_CLINICAL_RECOMMENDATIONS,
    AMD_URGENT_REFERRAL_INDICATORS,
    AMD_DISCLAIMER,
    AMD_CONSULTATION_TEMPLATE,
    AMD_KEYWORDS,
    get_consultation_type,
    format_patient_context
)

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

# Try to import TavilySearch, make it optional for local testing
try:
    from langchain_tavily import TavilySearch
    TAVILY_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: langchain_tavily not available. Web search will be disabled.")
    TavilySearch = None
    TAVILY_AVAILABLE = False

# Load environment variables (try .env file for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get TAVILY_API_KEY from environment
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# Initialize Tavily search tool
web_search_tool = None
if TAVILY_AVAILABLE and TAVILY_API_KEY:
    try:
        web_search_tool = TavilySearch(api_key=TAVILY_API_KEY, max_results=3)
        print("✅ Tavily search tool initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize Tavily search tool: {e}")
        web_search_tool = None
elif not TAVILY_AVAILABLE:
    print("⚠️ Warning: langchain_tavily not installed. Web search will not be available.")
elif not TAVILY_API_KEY:
    print("⚠️ Warning: TAVILY_API_KEY not found. Web search will not be available.")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_ssm_parameter(parameter_name: str) -> Optional[str]:
    """Get parameter from SSM"""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception:
        return None


def get_lambda_url() -> Optional[str]:
    """Get the Lambda Function URL from SSM"""
    return get_ssm_parameter("/app/medicalassistant/agentcore/lambda_url")


def get_current_user_id() -> Optional[str]:
    """Get the current user's Cognito user ID from the session context"""
    user_id = os.environ.get('AGENTCORE_USER_ID')
    if user_id:
        return user_id
    
    session_user = os.environ.get('AGENTCORE_SESSION_USER')
    if session_user:
        try:
            user_data = json.loads(session_user)
            return user_data.get('sub') or user_data.get('user_id')
        except (json.JSONDecodeError, AttributeError):
            pass
    
    test_user_id = os.environ.get('TEST_USER_ID')
    if test_user_id:
        return test_user_id
    
    return None


def get_patient_id_for_current_user() -> Optional[str]:
    """Get the patient_id for the currently authenticated user"""
    user_id = get_current_user_id()
    if not user_id:
        return None
    return user_id


def _query_knowledge_base_internal(query: str, kb_name: str = "diabetes-agent-kb"):
    """Internal helper function to query the medical knowledge base"""
    try:
        print(f"---KNOWLEDGE BASE QUERY---")
        print(f"Query: {query}")
        print(f"KB Name: {kb_name}")
        
        session = boto3.Session()
        region_name = session.region_name or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        print(f"Using AWS region: {region_name}")
        
        ssm_client = boto3.client('ssm', region_name=region_name)
        parameter_name = f"/bedrock/knowledge-base/{kb_name}/kb-id"
        
        try:
            response = ssm_client.get_parameter(Name=parameter_name)
            kb_id = response['Parameter']['Value']
            print(f"Found KB ID: {kb_id}")
        except ssm_client.exceptions.ParameterNotFound:
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


# =============================================================================
# SPECIALIST CONSULTATION TOOLS
# =============================================================================

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
        patient_context (str): Optional context about the patient
    
    Returns:
        str: Comprehensive diabetes consultation response with evidence-based recommendations
    """
    try:
        print(f"---DIABETES SPECIALIST CONSULTATION---")
        print(f"Patient Query: {patient_query}")
        print(f"Patient Context: {patient_context}")
        
        enhanced_query = f"diabetes {patient_query}"
        if patient_context:
            enhanced_query += f" {patient_context}"
        
        kb_results = _query_knowledge_base_internal(enhanced_query, "diabetes-agent-kb")
        
        consultation_type = get_consultation_type(patient_query, DIABETES_KEYWORDS)
        
        specialist_guidance = DIABETES_CONSULTATION_FRAMEWORKS.get(
            consultation_type, 
            DIABETES_CONSULTATION_FRAMEWORKS["general"]
        )
        
        patient_context_section = format_patient_context(patient_context)
        
        response = DIABETES_CONSULTATION_TEMPLATE.format(
            patient_query=patient_query,
            patient_context_section=patient_context_section,
            specialist_guidance=specialist_guidance,
            kb_results=kb_results,
            clinical_recommendations=DIABETES_CLINICAL_RECOMMENDATIONS,
            disclaimer=DIABETES_DISCLAIMER
        )
        
        print(f"Generated specialized diabetes consultation response")
        return response
        
    except Exception as e:
        error_msg = f"Error in diabetes specialist consultation: {str(e)}"
        print(error_msg)
        return error_msg


@tool
def amd_specialist_tool(patient_query: str, patient_context: str = ""):
    """
    Specialized Age-related Macular Degeneration (AMD) consultation tool.
    
    This tool combines knowledge base search with specialized AMD expertise to provide:
    - Early detection and risk assessment
    - Dry vs wet AMD differentiation
    - Treatment options and management strategies
    - Vision preservation techniques
    - Lifestyle modifications and supplements
    - Monitoring and follow-up recommendations
    
    Args:
        patient_query (str): The patient's question or concern about AMD or vision problems
        patient_context (str): Optional context about the patient
    
    Returns:
        str: Comprehensive AMD consultation response with evidence-based recommendations
    """
    try:
        print(f"---AMD SPECIALIST CONSULTATION---")
        print(f"Patient Query: {patient_query}")
        print(f"Patient Context: {patient_context}")
        
        enhanced_query = f"age-related macular degeneration AMD {patient_query}"
        if patient_context:
            enhanced_query += f" {patient_context}"
        
        kb_results = _query_knowledge_base_internal(enhanced_query, "diabetes-agent-kb")
        
        consultation_type = get_consultation_type(patient_query, AMD_KEYWORDS)
        
        specialist_guidance = AMD_CONSULTATION_FRAMEWORKS.get(
            consultation_type, 
            AMD_CONSULTATION_FRAMEWORKS["general"]
        )
        
        patient_context_section = format_patient_context(patient_context)
        
        response = AMD_CONSULTATION_TEMPLATE.format(
            patient_query=patient_query,
            patient_context_section=patient_context_section,
            specialist_guidance=specialist_guidance,
            kb_results=kb_results,
            clinical_recommendations=AMD_CLINICAL_RECOMMENDATIONS,
            urgent_referral_indicators=AMD_URGENT_REFERRAL_INDICATORS,
            disclaimer=AMD_DISCLAIMER
        )
        
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

    if web_search_tool is None:
        if not TAVILY_AVAILABLE:
            error_msg = "Web search is not available. langchain_tavily package is not installed."
        elif not TAVILY_API_KEY:
            error_msg = "Web search is not available. TAVILY_API_KEY not configured in environment variables."
        else:
            error_msg = "Web search is not available. Tavily search tool initialization failed."
        print(f"❌ {error_msg}")
        return error_msg

    try:
        docs = web_search_tool.invoke({"query": query})
        
        print(f"Raw web search response: {docs}")
        print(f"Type of docs: {type(docs)}")
        
        if not docs:
            return f"No web search results found for query: {query}"

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


# =============================================================================
# PERSONAL MEDICATION TOOLS (Privacy-Safe)
# =============================================================================

@tool
def get_my_medications() -> str:
    """
    Get YOUR current medication list.
    
    This tool shows the medications for the currently logged-in user only.
    No patient ID or medical record number is needed - it automatically uses
    your authenticated session to retrieve your personal medication information.
    
    Returns:
        Your current medications with details including medication name, dosage,
        frequency, status, and instructions.
    """
    try:
        patient_id = get_patient_id_for_current_user()
        
        if not patient_id:
            return """❌ **Authentication Required**

I cannot access your medication information because you are not logged in.

Please sign in to view your medications."""
        
        lambda_url = get_lambda_url()
        if not lambda_url:
            return "❌ Medication database is temporarily unavailable. Please try again later."
        
        base_url = lambda_url.rstrip('/')
        medications_payload = {
            "action": "get_patient_medications",
            "patient_id": patient_id
        }
        
        med_response = requests.post(base_url, json=medications_payload, timeout=30)
        
        if med_response.status_code == 200:
            med_data = med_response.json()
            
            if med_data.get('status') == 'success':
                medications = med_data.get('medications', [])
                
                summary = "💊 **Your Current Medications**\n\n"
                
                if not medications:
                    summary += "📋 **No medications found in your record.**\n\n"
                    summary += "You currently have no recorded medications in the system.\n\n"
                    summary += "⚠️ If you are taking medications, please inform your healthcare provider to update your records."
                    return summary
                
                active_meds = [m for m in medications if m.get('medication_status') == 'Active']
                discontinued_meds = [m for m in medications if m.get('medication_status') == 'Discontinued']
                completed_meds = [m for m in medications if m.get('medication_status') == 'Completed']
                
                if active_meds:
                    summary += f"✅ **Active Medications ({len(active_meds)}):**\n\n"
                    for i, med in enumerate(active_meds, 1):
                        summary += f"{i}. **{med.get('medication_name', 'Unknown')}**"
                        if med.get('generic_name'):
                            summary += f" ({med.get('generic_name')})"
                        summary += "\n"
                        summary += f"   - **Dosage:** {med.get('dosage', 'N/A')}\n"
                        summary += f"   - **How to take:** {med.get('frequency', 'N/A')}\n"
                        summary += f"   - **Route:** {med.get('route', 'N/A')}\n"
                        if med.get('prescription_date'):
                            summary += f"   - **Prescribed:** {med.get('prescription_date')}\n"
                        if med.get('refills_remaining') is not None:
                            summary += f"   - **Refills remaining:** {med.get('refills_remaining')}\n"
                        if med.get('instructions'):
                            summary += f"   - **Instructions:** {med.get('instructions')}\n"
                        if med.get('notes'):
                            summary += f"   - **Notes:** {med.get('notes')}\n"
                        summary += "\n"
                
                if discontinued_meds:
                    summary += f"⏸️ **Discontinued Medications ({len(discontinued_meds)}):**\n\n"
                    for i, med in enumerate(discontinued_meds, 1):
                        summary += f"{i}. **{med.get('medication_name', 'Unknown')}**"
                        if med.get('generic_name'):
                            summary += f" ({med.get('generic_name')})"
                        summary += "\n"
                        summary += f"   - **Dosage:** {med.get('dosage', 'N/A')}\n"
                        if med.get('discontinuation_reason'):
                            summary += f"   - **Reason discontinued:** {med.get('discontinuation_reason')}\n"
                        if med.get('end_date'):
                            summary += f"   - **Discontinued on:** {med.get('end_date')}\n"
                        summary += "\n"
                
                if completed_meds:
                    summary += f"✔️ **Completed Courses ({len(completed_meds)}):**\n\n"
                    for i, med in enumerate(completed_meds, 1):
                        summary += f"{i}. **{med.get('medication_name', 'Unknown')}** - {med.get('dosage', 'N/A')}\n"
                        if med.get('start_date') and med.get('end_date'):
                            summary += f"   - **Duration:** {med.get('start_date')} to {med.get('end_date')}\n"
                        if med.get('notes'):
                            summary += f"   - **Notes:** {med.get('notes')}\n"
                        summary += "\n"
                
                summary += "\n⚠️ **Important:** Always verify your current medications with your healthcare provider before making any changes."
                
                return summary
            else:
                return f"❌ Error retrieving your medications: {med_data.get('message', 'Unknown error')}"
        else:
            return f"❌ Error accessing medication database (Status: {med_response.status_code})"
            
    except requests.exceptions.Timeout:
        return "❌ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to medication database. Please check your connection."
    except Exception as e:
        return f"❌ Error retrieving your medications. Please try again later."


@tool
def check_my_medication(medication_name: str) -> str:
    """
    Check if YOU are currently taking a specific medication.
    
    This tool checks your personal medication list to see if you're taking
    a particular medication. No patient ID needed - uses your authenticated session.
    
    Args:
        medication_name: Name of the medication to check (e.g., "Metformin", "Lisinopril")
        
    Returns:
        Information about whether you're taking this medication and details if found
    """
    try:
        medications_result = get_my_medications()
        
        if "❌" in medications_result:
            return medications_result
        
        if "No medications found" in medications_result:
            return f"📋 You are not currently taking {medication_name}.\n\nYou have no medications recorded in the system."
        
        search_term = medication_name.lower()
        
        if search_term in medications_result.lower():
            lines = medications_result.split('\n')
            result_lines = []
            found = False
            capture = False
            
            for i, line in enumerate(lines):
                if search_term in line.lower() and '**' in line:
                    found = True
                    capture = True
                    result_lines.append(f"✅ **Yes, you are taking {medication_name}**\n")
                
                if capture:
                    result_lines.append(line)
                    if line.strip() == '' and len(result_lines) > 5:
                        break
            
            if found:
                return '\n'.join(result_lines)
        
        return f"📋 **No, you are not currently taking {medication_name}.**\n\nThis medication is not in your active medication list."
        
    except Exception as e:
        return f"❌ Error checking medication. Please try again later."


# =============================================================================
# APPOINTMENT MANAGEMENT TOOLS
# =============================================================================

@tool
def get_appointments(
    patient_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Retrieve YOUR appointments with optional filters.
    
    This tool shows appointments for the currently logged-in user only.
    No patient ID needed - uses your authenticated session automatically.
    
    Args:
        provider_id: Filter by specific provider (optional)
        status: Filter by status - Scheduled, Confirmed, Cancelled, Completed, No-Show (optional)
        start_date: Filter from this date YYYY-MM-DD (optional)
        end_date: Filter until this date YYYY-MM-DD (optional)
    
    Returns:
        Your appointments with details
    """
    try:
        # If no patient_id provided, use current user
        if not patient_id:
            patient_id = get_patient_id_for_current_user()
            if not patient_id:
                return """❌ **Authentication Required**

I cannot access your appointment information because you are not logged in.

Please sign in to view your appointments."""
        
        lambda_url = get_lambda_url()
        if not lambda_url:
            return "❌ Appointment database is temporarily unavailable. Please try again later."
        
        base_url = lambda_url.rstrip('/')
        appointments_payload = {
            "action": "get_patient_appointments",
            "patient_id": patient_id
        }
        
        # Add optional filters
        if status:
            appointments_payload['status'] = status
        if start_date:
            appointments_payload['start_date'] = start_date
        if end_date:
            appointments_payload['end_date'] = end_date
        
        appt_response = requests.post(base_url, json=appointments_payload, timeout=30)
        
        if appt_response.status_code == 200:
            appt_data = appt_response.json()
            
            if appt_data.get('status') == 'success':
                appointments = appt_data.get('appointments', [])
                
                summary = "📅 **Your Appointments**\n\n"
                
                if not appointments:
                    summary += "📋 **No appointments found.**\n\n"
                    summary += "You currently have no scheduled appointments in the system.\n\n"
                    summary += "💡 To schedule an appointment, please contact your healthcare provider."
                    return summary
                
                # Group by status
                upcoming = [a for a in appointments if a.get('appointment_status') in ['Scheduled', 'Confirmed']]
                completed = [a for a in appointments if a.get('appointment_status') == 'Completed']
                cancelled = [a for a in appointments if a.get('appointment_status') in ['Cancelled', 'No Show']]
                
                if upcoming:
                    summary += f"🔜 **Upcoming Appointments ({len(upcoming)}):**\n\n"
                    for i, appt in enumerate(upcoming, 1):
                        summary += f"{i}. **{appt.get('appointment_type', 'Appointment')}**\n"
                        summary += f"   - **Date:** {appt.get('scheduled_date')} at {appt.get('scheduled_time')}\n"
                        summary += f"   - **Provider:** {appt.get('provider_name', 'N/A')}"
                        if appt.get('provider_specialty'):
                            summary += f" ({appt.get('provider_specialty')})"
                        summary += "\n"
                        if appt.get('facility_name'):
                            summary += f"   - **Location:** {appt.get('facility_name')}"
                            if appt.get('facility_city'):
                                summary += f", {appt.get('facility_city')}, {appt.get('facility_state')}"
                            summary += "\n"
                        if appt.get('appointment_reason'):
                            summary += f"   - **Reason:** {appt.get('appointment_reason')}\n"
                        summary += f"   - **Duration:** {appt.get('duration_minutes', 30)} minutes\n"
                        summary += f"   - **Status:** {appt.get('appointment_status')}\n"
                        if appt.get('scheduling_notes'):
                            summary += f"   - **Notes:** {appt.get('scheduling_notes')}\n"
                        summary += "\n"
                
                if completed:
                    summary += f"✅ **Past Appointments ({len(completed)}):**\n\n"
                    for i, appt in enumerate(completed[:5], 1):  # Show last 5
                        summary += f"{i}. **{appt.get('appointment_type')}** - {appt.get('scheduled_date')}\n"
                        summary += f"   - Provider: {appt.get('provider_name', 'N/A')}\n"
                        if appt.get('appointment_reason'):
                            summary += f"   - Reason: {appt.get('appointment_reason')}\n"
                        summary += "\n"
                    if len(completed) > 5:
                        summary += f"   ... and {len(completed) - 5} more past appointments\n\n"
                
                if cancelled:
                    summary += f"❌ **Cancelled/No-Show ({len(cancelled)}):**\n\n"
                    for i, appt in enumerate(cancelled[:3], 1):  # Show last 3
                        summary += f"{i}. **{appt.get('appointment_type')}** - {appt.get('scheduled_date')}\n"
                        summary += f"   - Status: {appt.get('appointment_status')}\n\n"
                
                summary += "\n💡 **Need to schedule?** Contact your healthcare provider to book an appointment."
                
                return summary
            else:
                return f"❌ Error retrieving your appointments: {appt_data.get('message', 'Unknown error')}"
        else:
            return f"❌ Error accessing appointment database (Status: {appt_response.status_code})"
            
    except requests.exceptions.Timeout:
        return "❌ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to appointment database. Please check your connection."
    except Exception as e:
        return f"❌ Error retrieving appointments. Please try again later."


@tool
def create_appointment(
    provider_id: str,
    appointment_date: str,
    appointment_type: str,
    reason_for_visit: str,
    facility_id: Optional[str] = None,
    duration_minutes: int = 30,
    notes: Optional[str] = None
) -> str:
    """
    Schedule a new appointment for yourself.
    
    This tool creates an appointment for the currently logged-in user.
    No patient ID needed - uses your authenticated session automatically.
    
    Args:
        provider_id: Provider UUID (required)
        appointment_date: Date and time in format YYYY-MM-DD HH:MM (required)
        appointment_type: Type like "Office Visit", "Follow-up", "Consultation" (required)
        reason_for_visit: Reason for the appointment (required)
        facility_id: Facility UUID (optional)
        duration_minutes: Duration in minutes (default: 30)
        notes: Additional notes (optional)
    
    Returns:
        Confirmation of appointment creation
    """
    try:
        patient_id = get_patient_id_for_current_user()
        if not patient_id:
            return """❌ **Authentication Required**

I cannot schedule an appointment because you are not logged in.

Please sign in to schedule appointments."""
        
        # Note: Appointment creation is not yet implemented in the database handler
        # This is a placeholder that will be implemented when appointment endpoints are added
        return """📅 **Appointment Scheduling Coming Soon**

The appointment scheduling feature is currently being developed and will be available soon.

To schedule an appointment now, please:
- Call your healthcare provider directly
- Use the patient portal
- Contact the front desk

We apologize for the inconvenience and appreciate your patience."""
            
    except Exception as e:
        return f"❌ Error creating appointment. Please try again later."
