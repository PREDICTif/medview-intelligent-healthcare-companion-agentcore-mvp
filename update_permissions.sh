#!/bin/bash
# Update IAM permissions for SSM and AgentCore Memory access

set -e

echo "🔧 Updating AgentCore IAM permissions for SSM and Memory access..."

# Deploy only the infrastructure stack to update permissions
pushd cdk > /dev/null
TIMESTAMP=$(date +%Y%m%d%H%M%S)
npx cdk deploy AgentCoreInfra --output "cdk.out.$TIMESTAMP" --no-cli-pager --require-approval never
popd > /dev/null

echo "✅ Permissions updated successfully!"
echo ""
echo "📋 The AgentCore runtime role now has permissions for:"
echo "   - SSM Parameter: /app/medicalassistant/agentcore/*"
echo "   - AgentCore Memory operations"
echo ""
echo "💡 You can now redeploy your agent and it should be able to access memory via SSM"