#!/usr/bin/env python3
"""
Simple test script for the Strands agent
"""
from strands import Agent, tool
from strands.models import BedrockModel
from tools import check_chunks_relevance, web_search, query_knowledge_base

def main():
    """Simple test function"""
    print("🤖 Testing Strands Agent...")
    
    # Create the agent
    model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    model = BedrockModel(model_id=model_id)
    
    agent = Agent(
        model=model,
        tools=[query_knowledge_base, check_chunks_relevance, web_search],
        system_prompt="""You're a specialized medical assistant focused on diabetes and healthcare information. You have access to these tools:

1. Query Knowledge Base: Search the medical knowledge base for diabetes and health information
2. Check chunks relevance: To evaluate if retrieved information is relevant to a question
3. Web search: To search the internet for current information (use only when knowledge base results are not relevant)

For medical questions, ALWAYS try the knowledge base first. Then evaluate relevance and use web search if needed."""
    )
    
    # Test prompts
    test_prompts = [
        "What is diabetes?",
        "What are the symptoms of diabetes?",
        "How is diabetes treated?",
        "What foods should diabetics avoid?",
        "What is the difference between type 1 and type 2 diabetes?",
        "What are the complications of diabetes?"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Testing: {prompt}")
        try:
            response = agent(prompt)
            response_text = response.message['content'][0]['text']
            print(f"🤖 Response: {response_text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()