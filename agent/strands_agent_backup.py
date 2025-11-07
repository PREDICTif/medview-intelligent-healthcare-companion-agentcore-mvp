import asyncio
import os
import json
from strands import Agent, tool
from typing import Generator, Union, Any
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel
from tools import web_search, diabetes_specialist_tool, amd_specialist_tool  # Import custom tools
from prompts import AGENT_SYSTEM_PROMPT  # Import centralized prompts
from patient_tools import lookup_patient_record, get_diabetes_patients_list, search_patients_by_name, get_patient_medication_list  # Import patient database tools
# from tools import check_chunks_relevance  # Commented out - can cause Lambda issues

# Set environment variable to bypass tool consent (as shown in AgentCore examples)
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Create the AgentCore app
app = BedrockAgentCoreApp()

model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
model = BedrockModel(
    model_id=model_id,
    # Configure model parameters for consistent medical information
    max_tokens=4096,
    temperature=0.1,  # Lower temperature for more consistent medical information
    # top_p=0.9,  # Cannot use both temperature and top_p with this model
)

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

@app.entrypoint
async def strands_agent_bedrock(payload, context):
    """
    Async handler for agent invocation with streaming support
    
    IMPORTANT: Payload structure varies depending on invocation method:
    - Direct invocation (Python SDK, Console, agentcore CLI): {"prompt": "..."}
    - AWS SDK invocation (JS/Java/etc via InvokeAgentRuntimeCommand): {"input": {"prompt": "..."}}
    
    The AWS SDK automatically wraps payloads in an "input" field as part of the API contract.
    This function handles both formats for maximum compatibility.
    
    Streaming is enabled by default for better user experience.
    """
    print("context:\n-------\n", context)
    
    # Handle both dict and string payloads
    if isinstance(payload, str):
        payload = json.loads(payload)
    
    # Extract the prompt from the payload
    # Try AWS SDK format first (most common for production): {"input": {"prompt": "..."}}
    # Fall back to direct format: {"prompt": "..."}
    user_input = None
    stream = True  # Enable streaming by default
    actor_id = None
    session_id = None
    
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
            actor_id = payload["input"].get("actor_id")
            session_id = payload["input"].get("session_id")
            # Check if streaming is explicitly disabled
            stream = payload["input"].get("stream", True)
        else:
            user_input = payload.get("prompt")
            actor_id = payload.get("actor_id")
            session_id = payload.get("session_id")
            # Check if streaming is explicitly disabled
            stream = payload.get("stream", True)
    
    if not user_input:
        user_input = "No prompt found in input, please guide customer to create a json payload with prompt key"
    
    print("processing message:\n*******\n", user_input)
    
    # Note: Memory integration is handled by memory_hook_provider.py
    # The memory hooks automatically save conversations and retrieve context
    
    # Use streaming response for better user experience
    if stream:
        try:
            # Load conversation history into agent if available
            if conversation_history:
                # Create a temporary agent with conversation history
                temp_agent = Agent(
                    model=model,
                    tools=[diabetes_specialist_tool, amd_specialist_tool, web_search],
                    system_prompt=AGENT_SYSTEM_PROMPT + "\n\nNote: Use patient context provided to personalize responses, but don't mention outdated information explicitly.",
                    messages=conversation_history
                )
                agent_stream = temp_agent.stream_async(enhanced_input)
            else:
                agent_stream = agent.stream_async(enhanced_input)
            
            # Collect response for memory storage
            response_parts = []
            
            # Stream events with garbage filtering - WORKING APPROACH
            async for event in agent_stream:
                # Convert event to string to check for garbage
                event_str = str(event)
                
                # If it contains obvious garbage metadata, skip it
                if any(garbage in event_str for garbage in ['object at 0x', 'UUID(', 'event_loop_cycle_id', 'agent']):
                    continue
                
                # Collect response text for memory storage
                if hasattr(event, 'content') and event.content:
                    response_parts.append(event.content)
                elif isinstance(event, dict) and 'content' in event:
                    response_parts.append(event['content'])
                
                # Otherwise yield the event as normal
                yield event
            
            # Save assistant response to memory
            if response_parts:
                full_response = ''.join(str(part) for part in response_parts)
                memory_manager.save_assistant_message(full_response)
                
        except Exception as e:
            print(f"Streaming failed, falling back to regular response: {e}")
            # Fall back to non-streaming
            if conversation_history:
                temp_agent = Agent(
                    model=model,
                    tools=[diabetes_specialist_tool, amd_specialist_tool, web_search],
                    system_prompt=AGENT_SYSTEM_PROMPT + "\n\nNote: Use patient context provided to personalize responses, but don't mention outdated information explicitly.",
                    messages=conversation_history
                )
                response = temp_agent(enhanced_input)
            else:
                response = agent(enhanced_input)
            
            # Save assistant response to memory
            if hasattr(response, 'message'):
                memory_manager.save_assistant_message(str(response.message))
            
            yield {"result": response.message}
    else:
        # Non-streaming response
        if conversation_history:
            temp_agent = Agent(
                model=model,
                tools=[diabetes_specialist_tool, amd_specialist_tool, web_search],
                system_prompt=AGENT_SYSTEM_PROMPT + "\n\nNote: Use patient context provided to personalize responses, but don't mention outdated information explicitly.",
                messages=conversation_history
            )
            response = temp_agent(enhanced_input)
        else:
            response = agent(enhanced_input)
        
        # Save assistant response to memory
        if hasattr(response, 'message'):
            memory_manager.save_assistant_message(str(response.message))
        
        yield {"result": response.message}

def test_agent_setup():
    """Simple test to verify agent setup without async context issues"""
    print("🧪 Testing agent setup...")
    
    # Test that the agent is properly configured
    print(f"✅ Model ID: {model_id}")
    print(f"✅ Model configured: {type(model).__name__}")
    
    # Test tools (they're passed in during agent creation)
    tools_list = [diabetes_specialist_tool, amd_specialist_tool, web_search]
    print(f"✅ Tools available: {len(tools_list)}")
    
    # Get tool names safely
    tool_names = []
    for tool in tools_list:
        if hasattr(tool, 'name'):
            tool_names.append(tool.name)
        elif hasattr(tool, '__name__'):
            tool_names.append(tool.__name__)
        else:
            tool_names.append(str(type(tool).__name__))
    
    print(f"✅ Tool names: {tool_names}")
    
    # Test system prompt
    print(f"✅ System prompt length: {len(AGENT_SYSTEM_PROMPT)} characters")
    print(f"✅ Agent configured: {type(agent).__name__}")
    
    print("✅ Agent setup test completed successfully!")
    print("💡 To test streaming, deploy the agent and use agentcore invoke")

def test_agent_response():
    """Test the agent's response to a simple query"""
    print("🧪 Testing agent response...")
    
    try:
        # Test with a simple medical query
        test_query = "What are the main symptoms of diabetes?"
        print(f"📝 Query: {test_query}")
        
        # Test memory integration
        memory_manager.set_session_context("test_patient", "test_session")
        
        # Get user context (should be empty for new session)
        user_context = memory_manager.get_user_context(test_query)
        print(f"🧠 User context: {len(user_context)} characters")
        
        # Use the agent directly (non-streaming)
        response = agent(test_query)
        
        print("✅ Agent responded successfully!")
        print(f"📄 Response type: {type(response)}")
        
        # Try to extract the response content
        if hasattr(response, 'message'):
            message = response.message
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get('text', str(content[0]))
                    print(f"💬 Response preview: {text[:200]}...")
                    
                    # Save to memory for testing
                    memory_manager.save_conversation_turn(test_query, text)
                    print("🧠 Saved conversation to memory")
                else:
                    print(f"💬 Response content: {str(content)[:200]}...")
            else:
                print(f"💬 Response message: {str(message)[:200]}...")
        else:
            print(f"💬 Response: {str(response)[:200]}...")
            
        print("✅ Agent response test completed successfully!")
        
    except Exception as e:
        print(f"❌ Agent response test failed: {e}")
        print("💡 This is normal - the agent needs proper runtime context to work fully")

if __name__ == "__main__":
    # Uncomment to test agent response locally
    # test_agent_response()
    
    app.run()