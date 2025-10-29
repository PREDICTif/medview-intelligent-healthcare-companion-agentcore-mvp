from strands import Agent, tool
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel
from tools import check_chunks_relevance, web_search, query_knowledge_base  # Import custom tools

# Create the AgentCore app
app = BedrockAgentCoreApp()

model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
model = BedrockModel(
    model_id=model_id,
)

agent = Agent(
    model=model,
    tools=[query_knowledge_base, check_chunks_relevance, web_search],
    system_prompt="""You're a specialized medical assistant focused on diabetes and healthcare information. You have access to these tools:

1. Query Knowledge Base: Search the medical knowledge base for diabetes and health information
2. Check chunks relevance: To evaluate if retrieved information is relevant to a question
3. Web search: To search the internet for current information (use only when knowledge base results are not relevant)

For medical questions, ALWAYS try the knowledge base first using query_knowledge_base. Then use check_chunks_relevance to evaluate if the results are relevant. Only use web_search if the knowledge base results are not relevant (relevance score is 'no').

You specialize in diabetes, medical conditions, treatments, symptoms, diet, and general healthcare information."""
)

@app.entrypoint
def strands_agent_bedrock(payload):
    """
    Invoke the agent with a payload
    
    IMPORTANT: Payload structure varies depending on invocation method:
    - Direct invocation (Python SDK, Console, agentcore CLI): {"prompt": "..."}
    - AWS SDK invocation (JS/Java/etc via InvokeAgentRuntimeCommand): {"input": {"prompt": "..."}}
    
    The AWS SDK automatically wraps payloads in an "input" field as part of the API contract.
    This function handles both formats for maximum compatibility.
    """
    # Handle both dict and string payloads
    if isinstance(payload, str):
        payload = json.loads(payload)
    
    # Extract the prompt from the payload
    # Try AWS SDK format first (most common for production): {"input": {"prompt": "..."}}
    # Fall back to direct format: {"prompt": "..."}
    user_input = None
    if isinstance(payload, dict):
        if "input" in payload and isinstance(payload["input"], dict):
            user_input = payload["input"].get("prompt")
        else:
            user_input = payload.get("prompt")
    
    if not user_input:
        raise ValueError(f"No prompt found in payload. Expected {{'prompt': '...'}} or {{'input': {{'prompt': '...'}}}}. Received: {payload}")
    
    response = agent(user_input)
    response_text = response.message['content'][0]['text']
    
    return response_text

if __name__ == "__main__":
    app.run()
