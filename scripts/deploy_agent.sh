#!/bin/bash
# Quick deploy script for agent updates

set -e

echo "🚀 Deploying Agent to AgentCore..."
echo ""

# Check if we're in the right directory
if [ ! -d "../cdk" ]; then
    echo "❌ Error: Must run from scripts/ directory"
    exit 1
fi

# Navigate to CDK directory
cd ../cdk

echo "📦 Building and deploying agent runtime..."
echo ""

# Deploy the runtime (this builds the container and updates AgentCore)
npx cdk deploy AgentCoreRuntimeV2 --require-approval never --no-cli-pager

echo ""
echo "✅ Agent deployed successfully!"
echo ""
echo "🌐 Test in your web chat:"
echo "   1. Open your CloudFront URL"
echo "   2. Sign in with Cognito"
echo "   3. Ask: 'Show me medications for patient MRN-2024-001001'"
echo ""
