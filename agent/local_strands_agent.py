#!/usr/bin/env python3
"""
Local test script for the Strands agent
Run this to test your agent locally before deploying to AgentCore
"""
import json
import sys
from strands import Agent, tool
from strands.models import BedrockModel
from tools import check_chunks_relevance, web_search, query_knowledge_base

def create_agent():
    """Create and configure the agent"""
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
    
    return agent

def test_agent_with_prompt(agent, prompt):
    """Test the agent with a single prompt"""
    print(f"\n{'='*60}")
    print(f"User: {prompt}")
    print(f"{'='*60}")
    
    try:
        response = agent(prompt)
        response_text = response.message['content'][0]['text']
        print(f"Agent: {response_text}")
        return response_text
    except Exception as e:
        print(f"Error: {e}")
        return None

def interactive_mode(agent):
    """Run the agent in interactive mode"""
    print("\n🤖 Strands Agent - Interactive Mode")
    print("Type 'quit', 'exit', or 'q' to stop")
    print("Type 'help' for example prompts")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == 'help':
                print("\n📝 Example prompts to try:")
                print("• What is diabetes?")
                print("• What are the symptoms of diabetes?")
                print("• How is diabetes treated?")
                print("• What foods should diabetics avoid?")
                print("• What is the difference between type 1 and type 2 diabetes?")
                print("• What are the complications of diabetes?")
                print("• How can diabetes be prevented?")
                continue
            
            if not user_input:
                print("Please enter a prompt or type 'help' for examples.")
                continue
            
            test_agent_with_prompt(agent, user_input)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")

def run_test_suite(agent):
    """Run a predefined test suite"""
    print("\n🧪 Running Test Suite...")
    
    test_cases = [
        "What is diabetes?",
        "What are the symptoms of diabetes?",
        "How is diabetes treated?",
        "What foods should diabetics avoid?",
        "What is the difference between type 1 and type 2 diabetes?",
        "What are the complications of diabetes?",
        "How can diabetes be prevented?"
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{len(test_cases)}")
        result = test_agent_with_prompt(agent, test_case)
        results.append({
            'prompt': test_case,
            'response': result,
            'success': result is not None
        })
    
    # Summary
    successful_tests = sum(1 for r in results if r['success'])
    print(f"\n📊 Test Summary:")
    print(f"✅ Successful: {successful_tests}/{len(test_cases)}")
    print(f"❌ Failed: {len(test_cases) - successful_tests}/{len(test_cases)}")
    
    return results

def test_payload_formats(agent):
    """Test different payload formats that AgentCore might send"""
    print("\n🔧 Testing Payload Formats...")
    
    # Simulate the strands_agent_bedrock function locally
    def simulate_agentcore_invocation(payload):
        """Simulate how AgentCore would invoke the agent"""
        # Handle both dict and string payloads
        if isinstance(payload, str):
            payload = json.loads(payload)
        
        # Extract the prompt from the payload
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
    
    # Test different payload formats
    test_payloads = [
        {"prompt": "What's 2 + 2?"},  # Direct format
        {"input": {"prompt": "What's the weather?"}},  # AWS SDK format
        '{"prompt": "Calculate 10 * 5"}',  # JSON string format
        '{"input": {"prompt": "Is it sunny?"}}'  # JSON string AWS SDK format
    ]
    
    for i, payload in enumerate(test_payloads, 1):
        print(f"\n🧪 Payload Test {i}: {payload}")
        try:
            result = simulate_agentcore_invocation(payload)
            print(f"✅ Success: {result}")
        except Exception as e:
            print(f"❌ Failed: {e}")

def main():
    """Main function"""
    print("🚀 Strands Agent Local Tester")
    print("=" * 50)
    
    # Create the agent
    print("Creating agent...")
    try:
        agent = create_agent()
        print("✅ Agent created successfully!")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'test':
            # Run test suite
            run_test_suite(agent)
        elif mode == 'payload':
            # Test payload formats
            test_payload_formats(agent)
        elif mode == 'prompt':
            # Single prompt test
            if len(sys.argv) > 2:
                prompt = ' '.join(sys.argv[2:])
                test_agent_with_prompt(agent, prompt)
            else:
                print("Please provide a prompt: python local_strands_agent.py prompt 'What is 2+2?'")
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: test, payload, prompt, or no argument for interactive mode")
    else:
        # Interactive mode
        interactive_mode(agent)

if __name__ == "__main__":
    main()