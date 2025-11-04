import asyncio
import os
import json
from strands import Agent, tool
from typing import Generator, Union, Any
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel
from tools import web_search, diabetes_specialist_tool, amd_specialist_tool  # Import custom tools
from prompts import AGENT_SYSTEM_PROMPT  # Import centralized prompts
# from tools import check_chunks_relevance  # Commented out - can cause Lambda issues

# Set environment variable to bypass tool consent (as shown in AgentCore examples)
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Create the AgentCore app
app = BedrockAgentCoreApp()

model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
model = BedrockModel(
    model_id=model_id,
    # Configure model parameters for consistent medical information
    model_kwargs={
        "max_tokens": 4096,
        "temperature": 0.1,  # Lower temperature for more consistent medical information
        "top_p": 0.9,
    }
)

agent = Agent(
    model=model,
    tools=[diabetes_specialist_tool, amd_specialist_tool, web_search],
    # tools=[query_knowledge_base, check_chunks_relevance, web_search, check_aws_region],  # Full version with relevance check
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
    
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
            # Check if streaming is explicitly disabled
            stream = payload["input"].get("stream", True)
        else:
            user_input = payload.get("prompt")
            # Check if streaming is explicitly disabled
            stream = payload.get("stream", True)
    
    if not user_input:
        user_input = "No prompt found in input, please guide customer to create a json payload with prompt key"
    
    print("processing message:\n*******\n", user_input)
    
    # Use streaming response for better user experience
    if stream:
        try:
            # Get the agent stream using async method
            agent_stream = agent.stream_async(user_input)
            
            # Stream events with garbage filtering - WORKING APPROACH
            async for event in agent_stream:
                # Convert event to string to check for garbage
                event_str = str(event)
                
                # If it contains obvious garbage metadata, skip it
                if any(garbage in event_str for garbage in ['object at 0x', 'UUID(', 'event_loop_cycle_id', 'agent']):
                    continue
                
                # Otherwise yield the event as normal
                yield event
                
        except Exception as e:
            print(f"Streaming failed, falling back to regular response: {e}")
            # Fall back to non-streaming
            response = agent(user_input)
            yield {"result": response.message}
    else:
        # Non-streaming response
        response = agent(user_input)
        yield {"result": response.message}

def test_streaming():
    """Test function to verify streaming works locally"""
    test_payload = {"prompt": "What is diabetes?", "stream": True}
    
    print("Testing streaming response...")
    response = strands_agent_bedrock(test_payload)
    
    if hasattr(response, '__iter__') and not isinstance(response, str):
        # It's a generator (streaming)
        print("✅ Streaming enabled - receiving chunks:")
        for i, chunk in enumerate(response):
            print(f"Chunk {i+1}: {chunk}")
            if i > 10:  # Limit output for testing
                print("... (truncated)")
                break
    else:
        # It's a regular response
        print("⚠️ Non-streaming response:")
        print(response)

if __name__ == "__main__":
    # Uncomment to test streaming locally
    # test_streaming()
    app.run()
