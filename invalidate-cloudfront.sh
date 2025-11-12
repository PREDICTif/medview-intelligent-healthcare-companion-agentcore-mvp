#!/bin/bash

echo "🔄 Invalidating CloudFront Cache"
echo "================================"
echo ""

# Get CloudFront distribution ID from stack outputs
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name AgentCoreFrontend \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text 2>/dev/null)

# If not in outputs, try to find it from the distribution domain
if [ -z "$DISTRIBUTION_ID" ]; then
  CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name AgentCoreFrontend \
    --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
    --output text)
  
  DOMAIN=$(echo $CLOUDFRONT_URL | sed 's|https://||' | sed 's|/.*||')
  
  DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?DomainName=='$DOMAIN'].Id" \
    --output text)
fi

if [ -z "$DISTRIBUTION_ID" ]; then
  echo "❌ Could not find CloudFront distribution ID"
  echo ""
  echo "Manual steps:"
  echo "1. Go to AWS Console → CloudFront"
  echo "2. Find distribution for: d1kg75xyopexst.cloudfront.net"
  echo "3. Click on it → Invalidations tab"
  echo "4. Create invalidation with path: /*"
  exit 1
fi

echo "Distribution ID: $DISTRIBUTION_ID"
echo ""
echo "Creating invalidation for all files (/*) ..."

INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)

if [ $? -eq 0 ]; then
  echo "✅ Invalidation created: $INVALIDATION_ID"
  echo ""
  echo "⏳ Wait 2-3 minutes for invalidation to complete"
  echo ""
  echo "Then:"
  echo "1. Open application in incognito/private window"
  echo "2. Or hard refresh (Ctrl+Shift+R / Cmd+Shift+R)"
  echo "3. Sign in and test"
else
  echo "❌ Failed to create invalidation"
  exit 1
fi
