#!/bin/bash
# Deploy medical assistant agent with memory integration

set -e

echo "🏥 Deploying Medical Assistant Agent with Memory Integration"
echo "=========================================================="

# Check if memory exists, create if needed
echo "🧠 Checking memory setup..."

# Try to get existing memory ID first
MEMORY_ID=""
if MEMORY_ID=$(aws ssm get-parameter --name "/app/medicalassistant/agentcore/memory_id" --query "Parameter.Value" --output text 2>/dev/null); then
    echo "✅ Found existing memory ID: $MEMORY_ID"
else
    echo "📝 No existing memory found, creating new one..."
    
    # Create memory and capture output
    if python scripts/agentcore_memory.py create --name "ChatMemory" 2>&1; then
        # Try to get the memory ID after creation
        if MEMORY_ID=$(aws ssm get-parameter --name "/app/medicalassistant/agentcore/memory_id" --query "Parameter.Value" --output text 2>/dev/null); then
            echo "✅ Memory created successfully: $MEMORY_ID"
        else
            echo "⚠️ Memory created but could not retrieve ID from SSM"
            MEMORY_ID=""
        fi
    else
        echo "⚠️ Memory creation failed - continuing without memory"
        MEMORY_ID=""
    fi
fi

# Configure agent (same for both cases)
echo "⚙️ Configuring agent..."
agentcore configure --entrypoint agent/strands_agent.py --requirements-file agent/requirements.txt

# Launch with or without memory
if [ -z "$MEMORY_ID" ]; then
    echo "⚠️ No memory ID found - launching without memory"
    echo "🚀 Launching agent..."
    agentcore launch
else
    echo "✅ Memory ID found: $MEMORY_ID"
    echo "🚀 Launching agent with memory integration..."
    agentcore launch --env "AGENTCORE_MEMORY_ID=$MEMORY_ID"
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Test commands:"
echo "  # Basic test"
echo "  agentcore invoke '{\"prompt\": \"What are the symptoms of diabetes?\"}'"
echo ""
echo "  # Test with session (for memory)"
if [ ! -z "$MEMORY_ID" ]; then
    echo "  agentcore invoke '{\"prompt\": \"I have type 2 diabetes\"}' --session-id user123"
    echo "  agentcore invoke '{\"prompt\": \"What should I eat for breakfast?\"}' --session-id user123"
else
    echo "  # Memory not available - sessions won't persist"
fi
echo ""