#!/usr/bin/env python3
"""
Test the medications tool with the Strands agent locally.
This demonstrates how the agent uses the medication tool in conversation.
"""

import sys
import os
from pathlib import Path

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

# Set environment variables for local testing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['TAVILY_API_KEY'] = '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'

# Import after setting environment
from strands import Agent
from strands.models import BedrockModel
from patient_tools import (
    lookup_patient_record,
    get_patient_medication_list,
    search_patients_by_name,
    get_diabetes_patients_list
)
from prompts import AGENT_SYSTEM_PROMPT

def test_medications_with_agent():
    """Test the medications tool with the agent"""
    
    print("🤖 Initializing Medical Assistant Agent...")
    print("=" * 70)
    
    # Initialize the Bedrock model
    model = BedrockModel(
        inference_profile_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
        streaming=False
    )
    
    # Create agent with patient tools
    agent = Agent(
        model=model,
        tools=[
            lookup_patient_record,
            get_patient_medication_list,
            search_patients_by_name,
            get_diabetes_patients_list
        ],
        system_prompt=AGENT_SYSTEM_PROMPT
    )
    
    print("✅ Agent initialized with patient database tools\n")
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Get medications by MRN",
            "query": "Can you show me the medication list for patient MRN-2024-001001?"
        },
        {
            "name": "Get medications with patient lookup",
            "query": "What medications is Sarah Johnson taking? Her MRN is MRN-2024-001001."
        },
        {
            "name": "Check for specific medication",
            "query": "Is patient MRN-2024-001001 taking Metformin?"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'=' * 70}")
        print(f"Test Scenario {i}: {scenario['name']}")
        print(f"{'=' * 70}")
        print(f"\n👤 User: {scenario['query']}\n")
        
        try:
            # Run the agent
            response = agent(scenario['query'])
            
            # Extract the response message
            if hasattr(response, 'message'):
                if isinstance(response.message, dict):
                    content = response.message.get('content', str(response.message))
                else:
                    content = str(response.message)
            else:
                content = str(response)
            
            print(f"🤖 Agent: {content}\n")
            
            # Show tool usage if available
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print("🔧 Tools Used:")
                for tool_call in response.tool_calls:
                    print(f"   - {tool_call.get('name', 'unknown')}")
                print()
            
        except Exception as e:
            print(f"❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print(f"{'=' * 70}")
    print("✅ Testing complete!")
    print(f"{'=' * 70}\n")


def interactive_mode():
    """Run the agent in interactive mode"""
    
    print("🤖 Medical Assistant Agent - Interactive Mode")
    print("=" * 70)
    print("Type 'exit', 'quit', or 'bye' to end the session")
    print("=" * 70)
    print()
    
    # Initialize the Bedrock model
    model = BedrockModel(
        inference_profile_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="us-east-1",
        streaming=False
    )
    
    # Create agent with patient tools
    agent = Agent(
        model=model,
        tools=[
            lookup_patient_record,
            get_patient_medication_list,
            search_patients_by_name,
            get_diabetes_patients_list
        ],
        system_prompt=AGENT_SYSTEM_PROMPT
    )
    
    print("✅ Agent ready! Try asking:")
    print("   - 'Show me medications for patient MRN-2024-001001'")
    print("   - 'What medications is Sarah Johnson taking?'")
    print("   - 'Is patient MRN-2024-001001 on Metformin?'")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            print()
            
            # Run the agent
            response = agent(user_input)
            
            # Extract the response message
            if hasattr(response, 'message'):
                if isinstance(response.message, dict):
                    content = response.message.get('content', str(response.message))
                else:
                    content = str(response.message)
            else:
                content = str(response)
            
            print(f"🤖 Agent: {content}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test medications tool with the agent')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('--query', '-q', type=str,
                       help='Single query to test')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.query:
        # Single query mode
        print("🤖 Initializing Medical Assistant Agent...")
        
        model = BedrockModel(
            inference_profile_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name="us-east-1",
            streaming=False
        )
        
        agent = Agent(
            model=model,
            tools=[
                lookup_patient_record,
                get_patient_medication_list,
                search_patients_by_name,
                get_diabetes_patients_list
            ],
            system_prompt=AGENT_SYSTEM_PROMPT
        )
        
        print(f"\n👤 User: {args.query}\n")
        
        response = agent(args.query)
        
        if hasattr(response, 'message'):
            if isinstance(response.message, dict):
                content = response.message.get('content', str(response.message))
            else:
                content = str(response.message)
        else:
            content = str(response)
        
        print(f"🤖 Agent: {content}\n")
    else:
        # Run test scenarios
        test_medications_with_agent()
