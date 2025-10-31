#!/bin/bash

# Script to retrieve the Lambda Function URL from CloudFormation stack
# Usage: ./scripts/get-lambda-url.sh [stack-name]

STACK_NAME="${1:-MihcStack}"

echo "=========================================="
echo "Retrieving Lambda Function URL"
echo "Stack: $STACK_NAME"
echo "=========================================="

# Get the Lambda Function URL
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseLambdaFunctionUrl`].OutputValue' \
  --output text 2>/dev/null)

if [ -z "$FUNCTION_URL" ]; then
  echo "❌ Error: Could not retrieve Lambda Function URL"
  echo ""
  echo "Possible causes:"
  echo "  1. Stack '$STACK_NAME' does not exist"
  echo "  2. Stack has not been deployed yet"
  echo "  3. AWS credentials not configured"
  echo ""
  echo "To deploy the stack, run:"
  echo "  cd cdk"
  echo "  cdk deploy"
  exit 1
fi

echo ""
echo "✅ Lambda Function URL retrieved successfully:"
echo ""
echo "$FUNCTION_URL"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Copy the URL above"
echo ""
echo "2. Create/update frontend/.env.local with:"
echo ""
echo "   VITE_LAMBDA_FUNCTION_URL=$FUNCTION_URL"
echo ""
echo "3. Also add your Cognito configuration:"
echo ""
echo "   VITE_USER_POOL_ID=us-east-1_XXXXXXXXX"
echo "   VITE_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx"
echo ""
echo "4. Restart your frontend dev server:"
echo ""
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "=========================================="

