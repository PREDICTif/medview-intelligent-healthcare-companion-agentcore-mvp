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
from memory_hook_provider import MemoryHook
from strands.hooks import HookRegistry

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
    Extract Cognito user ID from AgentCore context
    
    Priority order:
    1. context.identity.sub (Cognito user ID from JWT token)
    2. context.identity.user_id (alternative user ID field)
    3. context.user_id (direct user ID)
    4. Fallback to session-based ID
    """
    print(f"🔍 Extracting user ID from context: {type(context)}")
    
    # Try to get Cognito sub (user ID) from identity
    if hasattr(context, 'identity') and context.identity:
        print(f"   Found identity object: {type(context.identity)}")
        
        # Cognito sub is the primary user identifier
        if hasattr(context.identity, 'sub') and context.identity.sub:
            cognito_user_id = context.identity.sub
            print(f"✅ Using Cognito user ID (sub): {cognito_user_id}")
            return cognito_user_id
        
        # Alternative user_id field
        if hasattr(context.identity, 'user_id') and context.identity.user_id:
            user_id = context.identity.user_id
            print(f"✅ Using identity user_id: {user_id}")
            return user_id
        
        # Check for username as fallback
        if hasattr(context.identity, 'username') and context.identity.username:
            username = context.identity.username
            print(f"✅ Using identity username: {username}")
            return username
    
    # Direct user_id on context
    if hasattr(context, 'user_id') and context.user_id:
        user_id = context.user_id
        print(f"✅ Using context user_id: {user_id}")
        return user_id
    
    # Fallback to session_id
    if hasattr(context, 'session_id') and context.session_id:
        session_based_id = f"user_{context.session_id}"
        print(f"⚠️ Using session-based ID: {session_based_id}")
        return session_based_id
    
    # Last resort default
    print("⚠️ Using default user ID")
    return "default_user"

def get_session_id_from_context(context) -> str:
    """Extract session ID from AgentCore context"""
    if hasattr(context, 'session_id') and context.session_id:
        return context.session_id
    return "default_session"

def create_agent_with_memory(memory_id: str, actor_id: str, session_id: str) -> Agent:
    """Create agent with memory hook configured"""
    model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    model = BedrockModel(
        model_id=model_id,
        max_tokens=4096,
        temperature=0.1,
    )
    
    # Create agent with patient database tools
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
        system_prompt=AGENT_SYSTEM_PROMPT
    )
    
    # Add memory hook if memory_id and memory_client are available
    if memory_id and memory_client:
        try:
            print(f"🧠 Configuring memory: memory_id={memory_id}, actor_id={actor_id}, session_id={session_id}")
            memory_hook = MemoryHook(
                memory_client=memory_client,
                memory_id=memory_id,
                actor_id=actor_id,
                session_id=session_id
            )
            
            # Register memory hooks
            hook_registry = HookRegistry()
            memory_hook.register_hooks(hook_registry)
            agent.hook_registry = hook_registry
            
            print("✅ Memory hooks registered successfully")
        except Exception as e:
            print(f"⚠️ Memory hook registration failed: {e}")
            print("🔄 Continuing without memory...")
    else:
        if not memory_id:
            print("⚠️ No memory_id available, running without memory")
        if not memory_client:
            print("⚠️ Memory client not available, running without memory")
    
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
    print("🚀 Medical Assistant Agent invoked!")
    print(f"📦 Payload: {payload}")
    print(f"🔧 Context: {context}")
    
    # Initialize memory and agent for this request
    memory_id = get_memory_id()
    actor_id = extract_user_id_from_context(context)
    session_id = get_session_id_from_context(context)
    
    print(f"🧠 Memory setup: memory_id={memory_id}, actor_id={actor_id}, session_id={session_id}")
    
    # Create agent with memory configuration and patient database tools
    agent = create_agent_with_memory(memory_id, actor_id, session_id)
    
    # Handle both dict and string payloads
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
            print("✅ Parsed string payload to dict")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            yield {"error": f"Invalid JSON payload: {e}"}
            return
    
    # Extract the prompt from the payload
    user_input = None
    stream = True  # Enable streaming by default
    
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
            stream = payload["input"].get("stream", True)
            print("📝 Using AWS SDK format (input wrapper)")
        else:
            user_input = payload.get("prompt")
            stream = payload.get("stream", True)
            print("📝 Using direct format")
    
    if not user_input:
        user_input = "No prompt found in input, please guide customer to create a json payload with prompt key"
        print("⚠️ No user input found, using default message")
    
    print("processing message:\n*******\n", user_input)
    print(f"streaming enabled: {stream}")
    
    # Use streaming response for better user experience
    if stream:
        try:
            print("🌊 Starting streaming response...")
            # Get the agent stream using async method
            agent_stream = agent.stream_async(user_input)
            
            event_count = 0
            yielded_count = 0
            has_yielded_content = False
            
            # Stream events with balanced filtering - clean but not too restrictive
            async for event in agent_stream:
                event_count += 1
                
                # Debug: print first few events
                if event_count <= 5:
                    print(f"Event {event_count}: {type(event)} - {str(event)[:100]}...")
                
                # Filter out complex objects but be more permissive
                try:
                    event_str = str(event)
                    
                    # Skip obvious garbage (object references)
                    if 'object at 0x' in event_str and len(event_str) < 200:
                        print(f"Skipping garbage event {event_count}")
                        continue
                    
                    # Try to extract text content from various event types
                    text_content = None
                    
                    if hasattr(event, 'data') and isinstance(event.data, str):
                        text_content = event.data
                    elif hasattr(event, 'delta') and hasattr(event.delta, 'text') and isinstance(event.delta.text, str):
                        text_content = event.delta.text
                    elif isinstance(event, str):
                        text_content = event
                    elif isinstance(event, dict):
                        if 'text' in event:
                            text_content = str(event['text'])
                        elif 'data' in event:
                            text_content = str(event['data'])
                        elif 'content' in event:
                            text_content = str(event['content'])
                    
                    # If we found text content, yield it
                    if text_content and text_content.strip():
                        yielded_count += 1
                        has_yielded_content = True
                        print(f"Yielding content {yielded_count}: '{text_content[:50]}...'")
                        yield {"text": text_content}
                    else:
                        # For debugging: yield the event as-is if it's not obviously garbage
                        if not ('object at 0x' in event_str or 'UUID(' in event_str or 'Trace object' in event_str):
                            yielded_count += 1
                            has_yielded_content = True
                            print(f"Yielding raw event {yielded_count}: {type(event)}")
                            yield event
                        else:
                            print(f"Skipping complex event {event_count}: {type(event)}")
                        
                except Exception as e:
                    print(f"Error processing event {event_count}: {e}")
                    # Try to yield the event anyway if it's not obviously garbage
                    try:
                        event_str = str(event)
                        if not ('object at 0x' in event_str or len(event_str) > 1000):
                            yielded_count += 1
                            has_yielded_content = True
                            yield event
                    except:
                        continue
            
            print(f"✅ Streaming completed: {event_count} total events, {yielded_count} yielded")
            
            # If no content was yielded, provide a fallback response
            if not has_yielded_content:
                print("⚠️ No content yielded from streaming, providing fallback")
                fallback_response = agent(user_input)
                yield {"result": fallback_response.message}
                
        except Exception as e:
            print(f"❌ Streaming failed: {e}")
            import traceback
            traceback.print_exc()
            
            print("🔄 Falling back to non-streaming...")
            # Fall back to non-streaming
            response = agent(user_input)
            print(f"Non-streaming response: {response.message}")
            yield {"result": response.message}
    else:
        print("📄 Using non-streaming response...")
        # Non-streaming response
        response = agent(user_input)
        print(f"Non-streaming response: {response.message}")
        yield {"result": response.message}

if __name__ == "__main__":
    # Local testing mode
    print("🧪 Running in local test mode")
    print("=" * 60)
    
    # Create a mock context for testing
    class MockIdentity:
        def __init__(self, sub=None, user_id=None, username=None):
            self.sub = sub  # Cognito user ID
            self.user_id = user_id
            self.username = username
    
    class MockContext:
        def __init__(self, identity=None, session_id=None, user_id=None):
            self.identity = identity
            self.session_id = session_id
            self.user_id = user_id
    
    # Test different context scenarios
    print("\n📋 Testing user ID extraction:")
    print("-" * 60)
    
    # Test 1: With Cognito sub (most common in production)
    print("\n1️⃣ Test with Cognito sub:")
    mock_identity = MockIdentity(sub="cognito-user-123-abc-def")
    mock_context = MockContext(identity=mock_identity, session_id="session-456")
    user_id = extract_user_id_from_context(mock_context)
    print(f"   Result: {user_id}")
    assert user_id == "cognito-user-123-abc-def", "Should use Cognito sub"
    
    # Test 2: With user_id in identity
    print("\n2️⃣ Test with identity.user_id:")
    mock_identity = MockIdentity(user_id="user-789")
    mock_context = MockContext(identity=mock_identity, session_id="session-456")
    user_id = extract_user_id_from_context(mock_context)
    print(f"   Result: {user_id}")
    assert user_id == "user-789", "Should use identity.user_id"
    
    # Test 3: With username fallback
    print("\n3️⃣ Test with username:")
    mock_identity = MockIdentity(username="john.doe@example.com")
    mock_context = MockContext(identity=mock_identity, session_id="session-456")
    user_id = extract_user_id_from_context(mock_context)
    print(f"   Result: {user_id}")
    assert user_id == "john.doe@example.com", "Should use username"
    
    # Test 4: With session fallback
    print("\n4️⃣ Test with session fallback:")
    mock_context = MockContext(session_id="session-789")
    user_id = extract_user_id_from_context(mock_context)
    print(f"   Result: {user_id}")
    assert user_id == "user_session-789", "Should use session-based ID"
    
    # Test 5: Default fallback
    print("\n5️⃣ Test with default fallback:")
    mock_context = MockContext()
    user_id = extract_user_id_from_context(mock_context)
    print(f"   Result: {user_id}")
    assert user_id == "default_user", "Should use default"
    
    print("\n" + "=" * 60)
    print("✅ All user ID extraction tests passed!")
    print("\n💡 In production, AgentCore will provide:")
    print("   - context.identity.sub = Cognito user ID (UUID)")
    print("   - context.session_id = Session identifier")
    print("   - These will be used for memory and personalization")
    print("\n🚀 To run the agent locally, use:")
    print("   app.run()")
    print("=" * 60)