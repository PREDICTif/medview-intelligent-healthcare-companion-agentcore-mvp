import asyncio
import os
import json
import boto3
from strands import Agent, tool
from typing import Generator, Union, Any
from bedrock_agentcore.runtime import BedrockAgentCoreApp
# from bedrock_agentcore.context import RequestContext  # May not be available in all environments
from strands.models import BedrockModel
from tools import web_search, diabetes_specialist_tool, amd_specialist_tool
from prompts import AGENT_SYSTEM_PROMPT
from patient_tools import lookup_patient_record, get_diabetes_patients_list, search_patients_by_name, get_patient_medication_list

# Import memory components
from bedrock_agentcore.memory import MemoryClient

# Set environment variable to bypass tool consent
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Initialize AWS clients with error handling
try:
    ssm = boto3.client("ssm")
    print("✅ SSM client initialized")
except Exception as e:
    print(f"⚠️ SSM client initialization failed: {e}")
    ssm = None

try:
    memory_client = MemoryClient()
    print("✅ Memory client initialized")
except Exception as e:
    print(f"⚠️ Memory client initialization failed: {e}")
    memory_client = None

def get_memory_id():
    """Get memory ID from environment variable or SSM parameter"""
    # First try environment variable (for AgentCore deployment)
    memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
    if memory_id:
        print(f"✅ Retrieved memory_id from environment: {memory_id}")
        return memory_id
    
    # Fallback to SSM parameter (for local testing)
    if not ssm:
        print("⚠️ SSM client not available and no AGENTCORE_MEMORY_ID env var - running without memory")
        return None
        
    try:
        response = ssm.get_parameter(Name="/app/medicalassistant/agentcore/memory_id")
        memory_id = response["Parameter"]["Value"]
        print(f"✅ Retrieved memory_id from SSM: {memory_id}")
        return memory_id
    except Exception as e:
        # Handle all SSM exceptions gracefully
        error_type = type(e).__name__
        if "ParameterNotFound" in error_type:
            print("⚠️ Memory parameter not found in SSM - running without memory")
        elif "AccessDenied" in error_type:
            print("⚠️ Access denied to SSM parameter - check IAM permissions")
        else:
            print(f"⚠️ SSM error (running without memory): {error_type}: {e}")
        return None

def extract_user_id_from_context(context) -> str:
    """
    Extract user ID from AgentCore context
    
    The frontend sends a user-specific session_id in format: user_<cognito_user_id>_session
    This allows us to use the session_id directly as a stable user identifier for memory.
    """
    # Use session_id directly - frontend sends user-specific session ID
    if hasattr(context, 'session_id') and context.session_id:
        session_id = context.session_id
        
        # Check if this is a user-specific session ID (format: user_<cognito_user_id>_session)
        if session_id.startswith('user_') and '_session' in session_id:
            # Extract the user ID from the session ID
            # Format: user_94c894a8-e0c1-7059-39f2-0cbe3c207746_session
            user_id = session_id.replace('user_', '').replace('_session', '')
            return user_id
        else:
            # Legacy session ID format - use as-is
            return session_id
    
    # Last resort default
    return "default_user"

def get_session_id_from_context(context) -> str:
    """Extract session ID from AgentCore context"""
    if hasattr(context, 'session_id') and context.session_id:
        return context.session_id
    return "default_session"

def create_agent_with_memory(memory_id: str, actor_id: str, session_id: str) -> Agent:
    """Create agent with AgentCore Memory session manager"""
    model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    model = BedrockModel(
        model_id=model_id,
        max_tokens=4096,
        temperature=0.1,
    )
    
    # Configure AgentCore Memory session manager if available
    session_manager = None
    if memory_id:
        try:
            from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
            from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
            
            # Create memory configuration
            memory_config = AgentCoreMemoryConfig(
                memory_id=memory_id,
                session_id=session_id,
                actor_id=actor_id
            )
            
            # Create session manager
            session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=memory_config,
                region_name="us-east-1"
            )
        except Exception as e:
            print(f"Memory configuration failed: {e}")
            session_manager = None
    
    # Create agent with patient database tools and session manager
    agent = Agent(
        model=model,
        tools=[
            diabetes_specialist_tool, 
            amd_specialist_tool, 
            web_search,
            lookup_patient_record,           # Patient database lookup
            get_diabetes_patients_list,      # List diabetes patients  
            search_patients_by_name,         # Search patients by name
            get_patient_medication_list      # Get patient medications
        ],
        system_prompt=AGENT_SYSTEM_PROMPT,
        session_manager=session_manager  # Pass session manager to agent
    )
    
    return agent

@app.entrypoint
async def strands_agent_bedrock(payload, context):
    """
    Medical Assistant Agent with Patient Database Integration
    
    Features:
    - Diabetes and AMD specialist consultations
    - Web search for latest medical information  
    - Patient database lookup and search
    - Memory integration for conversation persistence
    - Streaming response support
    """
    # Initialize memory and agent for this request
    memory_id = get_memory_id()
    actor_id = extract_user_id_from_context(context)
    session_id = get_session_id_from_context(context)
    
    # Create agent with memory configuration and patient database tools
    agent = create_agent_with_memory(memory_id, actor_id, session_id)
    
    # Handle both dict and string payloads
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as e:
            yield {"error": f"Invalid JSON payload: {e}"}
            return
    
    # Extract the prompt from the payload
    user_input = None
    stream = True  # Enable streaming by default
    
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
            stream = payload["input"].get("stream", True)
        else:
            user_input = payload.get("prompt")
            stream = payload.get("stream", True)
    
    if not user_input:
        user_input = "No prompt found in input, please guide customer to create a json payload with prompt key"
    
    # Use streaming response for better user experience
    if stream:
        try:
            # Get the agent stream using async method
            agent_stream = agent.stream_async(user_input)
            
            has_yielded_content = False
            
            # Stream events - only yield the actual event objects from Strands
            async for event in agent_stream:
                # Only yield the event as-is - let AgentCore and frontend handle parsing
                try:
                    # Skip internal Python objects
                    event_str = str(event)
                    if 'object at 0x' in event_str and len(event_str) < 200:
                        continue
                    
                    # Skip UUID and Trace objects
                    if 'UUID(' in event_str or 'Trace object' in event_str:
                        continue
                    
                    # Yield the event as-is - Strands events are already properly formatted
                    has_yielded_content = True
                    yield event
                        
                except Exception:
                    continue
            
            # If no content was yielded, provide a fallback response
            if not has_yielded_content:
                fallback_response = agent(user_input)
                yield {"result": fallback_response.message}
                
        except Exception as e:
            print(f"Streaming failed: {e}")
            # Fall back to non-streaming
            response = agent(user_input)
            yield {"result": response.message}
    else:
        # Non-streaming response
        response = agent(user_input)
        yield {"result": response.message}

if __name__ == "__main__":
    app.run()