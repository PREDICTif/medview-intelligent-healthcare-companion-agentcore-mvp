#!/usr/bin/env python3
"""
Test script to verify streaming response fix
"""

import asyncio
import sys
import os
sys.path.append('agent')

from strands_agent import create_agent_with_memory

async def test_streaming_response():
    """Test that streaming responses are clean without garbage data"""
    
    print("🧪 Testing Streaming Response Fix")
    print("=" * 50)
    
    # Create agent (without memory for testing)
    agent = create_agent_with_memory(None, "test_user", "test_session")
    
    # Test streaming with a simple question
    test_prompt = "What foods should diabetics avoid? Give me a brief answer."
    
    print(f"📝 Testing prompt: {test_prompt}")
    print("\n🌊 Streaming response:")
    print("-" * 30)
    
    try:
        # Get streaming response
        agent_stream = agent.stream_async(test_prompt)
        
        event_count = 0
        text_parts = []
        
        async for event in agent_stream:
            event_count += 1
            
            # Check what type of event we get
            print(f"Event {event_count}: {type(event)}")
            
            # Extract text content based on event structure
            if hasattr(event, 'data') and isinstance(event.data, str):
                text_parts.append(event.data)
                print(f"  Text: '{event.data}'")
            elif hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                text_parts.append(event.delta.text)
                print(f"  Delta: '{event.delta.text}'")
            elif isinstance(event, str):
                text_parts.append(event)
                print(f"  String: '{event}'")
            elif isinstance(event, dict) and 'text' in event:
                text_parts.append(event['text'])
                print(f"  Dict text: '{event['text']}'")
            else:
                print(f"  Other: {str(event)[:100]}...")
        
        print("-" * 30)
        print(f"✅ Processed {event_count} events")
        print(f"📄 Combined response: {''.join(text_parts)}")
        
        # Check for garbage data
        full_response = ''.join(text_parts)
        if 'object at 0x' in full_response:
            print("❌ Still contains garbage data!")
            return False
        else:
            print("✅ No garbage data detected!")
            return True
            
    except Exception as e:
        print(f"❌ Error during streaming test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_streaming_response())
    if result:
        print("\n🎉 Streaming fix test PASSED!")
    else:
        print("\n❌ Streaming fix test FAILED!")