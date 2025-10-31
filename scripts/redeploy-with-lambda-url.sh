#!/bin/bash
# Quick script to redeploy MihcStack (for Lambda URL) and rebuild/redeploy frontend
# This fixes the "Lambda function URL not configured" error in deployed apps

set -e

echo "=========================================="
echo "Redeploying MihcStack and Frontend"
echo "=========================================="
echo ""

# Step 1: Deploy/Update MihcStack to get Lambda Function URL
echo "[1/4] Deploying MihcStack (database and Lambda)..."
cd cdk
npx cdk deploy MihcStack --require-approval never
cd ..
echo "✓ MihcStack deployed"
echo ""

# Step 2: Get all required configuration from CloudFormation
echo "[2/4] Retrieving configuration from AWS..."
LAMBDA_FUNCTION_URL=$(aws cloudformation describe-stacks --stack-name MihcStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseLambdaFunctionUrl`].OutputValue' \
  --output text 2>/dev/null || echo "")

AGENT_RUNTIME_ARN=$(aws cloudformation describe-stacks --stack-name AgentCoreRuntime \
  --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" \
  --output text --no-cli-pager 2>/dev/null || echo "")

REGION=$(aws cloudformation describe-stacks --stack-name AgentCoreRuntime \
  --query "Stacks[0].Outputs[?OutputKey=='Region'].OutputValue" \
  --output text --no-cli-pager 2>/dev/null || echo "")

USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name AgentCoreAuth \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text --no-cli-pager 2>/dev/null || echo "")

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name AgentCoreAuth \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
  --output text --no-cli-pager 2>/dev/null || echo "")

# Validate we got all the values
if [ -z "$LAMBDA_FUNCTION_URL" ]; then
    echo "❌ Error: Could not retrieve Lambda Function URL from MihcStack"
    echo "Make sure MihcStack deployed successfully"
    exit 1
fi

if [ -z "$AGENT_RUNTIME_ARN" ] || [ -z "$REGION" ] || [ -z "$USER_POOL_ID" ] || [ -z "$USER_POOL_CLIENT_ID" ]; then
    echo "❌ Error: Could not retrieve all required configuration"
    echo "Make sure AgentCoreRuntime and AgentCoreAuth stacks are deployed"
    exit 1
fi

echo "✓ Configuration retrieved:"
echo "  Lambda Function URL: $LAMBDA_FUNCTION_URL"
echo "  Agent Runtime ARN: $AGENT_RUNTIME_ARN"
echo "  Region: $REGION"
echo "  User Pool ID: $USER_POOL_ID"
echo "  User Pool Client ID: $USER_POOL_CLIENT_ID"
echo ""

# Step 3: Rebuild frontend with Lambda URL
echo "[3/4] Rebuilding frontend with Lambda Function URL..."
./scripts/build-frontend.sh "$USER_POOL_ID" "$USER_POOL_CLIENT_ID" "$AGENT_RUNTIME_ARN" "$REGION" "$LAMBDA_FUNCTION_URL"
echo "✓ Frontend rebuilt"
echo ""

# Step 4: Redeploy frontend to S3+CloudFront
echo "[4/4] Redeploying frontend to S3+CloudFront..."
cd cdk
npx cdk deploy AgentCoreFrontend --require-approval never
cd ..
echo "✓ Frontend redeployed"
echo ""

# Get website URL
WEBSITE_URL=$(aws cloudformation describe-stacks --stack-name AgentCoreFrontend \
  --query "Stacks[0].Outputs[?OutputKey=='WebsiteUrl'].OutputValue" \
  --output text --no-cli-pager 2>/dev/null || echo "")

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Website URL: $WEBSITE_URL"
echo "Lambda Function URL: $LAMBDA_FUNCTION_URL"
echo ""
echo "The patient registration form should now work in your deployed app!"
echo "Note: CloudFront may take a few minutes to serve the updated frontend."
echo ""

