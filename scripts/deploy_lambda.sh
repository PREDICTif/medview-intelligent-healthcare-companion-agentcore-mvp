#!/bin/bash
# Deploy Lambda function with updated code

set -e

LAMBDA_DIR="../lambda/database-handler"
FUNCTION_NAME="MihcStack-DatabaseLambda78D2905C-ivldwCYquL1k"

echo "🚀 Deploying Lambda function..."
echo "Function: $FUNCTION_NAME"
echo ""

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "📦 Creating deployment package in $TEMP_DIR"

# Copy Lambda code
cp "$LAMBDA_DIR/index.py" "$TEMP_DIR/"

# Create zip file
cd "$TEMP_DIR"
zip -q function.zip index.py

echo "✅ Package created"

# Deploy to Lambda
echo "📤 Uploading to Lambda..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://function.zip \
    --region us-east-1 \
    --output json > /dev/null

echo "✅ Lambda function updated"

# Wait for update to complete
echo "⏳ Waiting for update to complete..."
aws lambda wait function-updated \
    --function-name "$FUNCTION_NAME" \
    --region us-east-1

echo "✅ Update complete"

# Clean up
cd -
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 Deployment successful!"
echo ""
echo "Test with:"
echo "  python test_medications.py --mrn MRN-2024-001001 -v"
