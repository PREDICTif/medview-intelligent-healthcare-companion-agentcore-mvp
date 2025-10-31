# Fix: "Lambda function URL not configured" in DEPLOYED APP

## The Problem

When you submit the patient registration form in your **deployed AWS application** (not local dev), you get:
```
Error: Lambda function URL not configured
```

## Root Cause

The issue occurs because:

1. **Environment variables are baked into the build at build-time** - Vite replaces `import.meta.env.VITE_*` with actual values during the build process
2. **Your deployed frontend was built BEFORE the Lambda Function URL existed** - The build had `undefined` for `VITE_LAMBDA_FUNCTION_URL`
3. **The deployed app on S3/CloudFront has the old build** - It cannot access environment variables at runtime

This is different from local development where you can use `.env.local` files.

## The Solution

You need to:
1. Deploy the MihcStack (creates Lambda Function URL)
2. Rebuild the frontend with the Lambda URL
3. Redeploy the frontend to S3/CloudFront

### Quick Fix (Automated Script)

Run this single command:

```bash
./scripts/redeploy-with-lambda-url.sh
```

This script will:
1. Deploy MihcStack with Lambda Function URL
2. Retrieve all configuration (Cognito, Lambda URL, etc.)
3. Rebuild the frontend with the Lambda URL baked in
4. Redeploy the frontend to S3+CloudFront

**Wait 5-10 minutes** for CloudFront to distribute the new build, then test your deployed app.

---

### Manual Fix (Step-by-Step)

If you prefer to do it manually:

#### Step 1: Deploy MihcStack

```bash
cd cdk
npx cdk deploy MihcStack --require-approval never
cd ..
```

This creates:
- Aurora Serverless v2 PostgreSQL database
- Lambda function for database operations
- **Lambda Function URL** for HTTP access

#### Step 2: Get Lambda Function URL

```bash
LAMBDA_URL=$(aws cloudformation describe-stacks --stack-name MihcStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseLambdaFunctionUrl`].OutputValue' \
  --output text)

echo $LAMBDA_URL
```

Copy this URL.

#### Step 3: Get Other Required Configuration

```bash
# Get Cognito config
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name AgentCoreAuth \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" \
  --output text --no-cli-pager)

USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name AgentCoreAuth \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" \
  --output text --no-cli-pager)

# Get AgentCore config
AGENT_RUNTIME_ARN=$(aws cloudformation describe-stacks --stack-name AgentCoreRuntime \
  --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" \
  --output text --no-cli-pager)

REGION=$(aws cloudformation describe-stacks --stack-name AgentCoreRuntime \
  --query "Stacks[0].Outputs[?OutputKey=='Region'].OutputValue" \
  --output text --no-cli-pager)
```

#### Step 4: Rebuild Frontend with Lambda URL

**macOS/Linux:**
```bash
./scripts/build-frontend.sh "$USER_POOL_ID" "$USER_POOL_CLIENT_ID" "$AGENT_RUNTIME_ARN" "$REGION" "$LAMBDA_URL"
```

**Windows (PowerShell):**
```powershell
.\scripts\build-frontend.ps1 -UserPoolId $USER_POOL_ID -UserPoolClientId $USER_POOL_CLIENT_ID -AgentRuntimeArn $AGENT_RUNTIME_ARN -Region $REGION -LambdaFunctionUrl $LAMBDA_URL
```

This rebuilds the frontend with `VITE_LAMBDA_FUNCTION_URL` baked into the code.

#### Step 5: Redeploy Frontend

```bash
cd cdk
npx cdk deploy AgentCoreFrontend --require-approval never
cd ..
```

This uploads the new build to S3 and invalidates the CloudFront cache.

#### Step 6: Wait and Test

**Important:** CloudFront caching means it takes 5-10 minutes for the new version to be available globally.

After waiting:
1. Go to your deployed app URL
2. Sign in
3. Navigate to "Register Patient"
4. Fill out and submit the form
5. Should work! 🎉

---

## Verification

### Check if Lambda URL is in your build

```bash
# After building, check if the URL is in the build
grep -r "lambda-url" frontend/dist/assets/*.js

# You should see your Lambda URL in the output
```

### Check CloudFormation Outputs

```bash
# Verify MihcStack has the Lambda URL output
aws cloudformation describe-stacks --stack-name MihcStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseLambdaFunctionUrl`]'
```

### Check CloudFront Distribution

```bash
# Get your CloudFront distribution
aws cloudformation describe-stacks --stack-name AgentCoreFrontend \
  --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
  --output text
```

### Test the Lambda Function Directly

```bash
LAMBDA_URL="<your-lambda-url>"

# Test health check
curl -X POST "$LAMBDA_URL" \
  -H "Content-Type: application/json" \
  -d '{"action":"health_check"}'

# Should return database configuration info
```

---

## Future Deployments

Going forward, when you run `./deploy-all.sh` or `./deploy-all.ps1`, the scripts will:
1. Automatically retrieve the Lambda Function URL from MihcStack
2. Include it in the frontend build
3. Deploy the frontend with the URL baked in

The fix has been integrated into the deployment scripts, so this issue won't happen again.

---

## Troubleshooting

### Error: "Stack MihcStack does not exist"

You need to deploy it first:
```bash
cd cdk
npx cdk deploy MihcStack --require-approval never
```

### Error: "Lambda Function URL is empty"

Check if the stack deployed successfully:
```bash
aws cloudformation describe-stack-events --stack-name MihcStack --max-items 10
```

### Frontend still shows old version after redeployment

CloudFront caching can take time. Force a hard refresh:
- Chrome/Firefox: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Safari: Cmd+Option+R

Or wait 10-15 minutes for CloudFront to propagate.

### Want to force immediate CloudFront invalidation?

```bash
# Get distribution ID
DIST_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='Amazon Bedrock AgentCore Demo - Frontend Distribution'].Id" \
  --output text)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"
```

---

## What Changed

These files were updated to fix the issue:

1. **scripts/build-frontend.sh** - Added Lambda URL parameter
2. **scripts/build-frontend.ps1** - Added Lambda URL parameter
3. **deploy-all.sh** - Retrieves Lambda URL from MihcStack
4. **deploy-all.ps1** - Retrieves Lambda URL from MihcStack
5. **cdk/lib/mihc-stack.ts** - Added Lambda Function URL with CORS
6. **scripts/redeploy-with-lambda-url.sh** - New quick fix script

All future deployments will automatically include the Lambda URL.

---

## Summary

**Problem:** Deployed app built without Lambda URL → `undefined` → error  
**Solution:** Rebuild with Lambda URL → Redeploy → Wait for CloudFront → Success! ✅

**Quick Command:**
```bash
./scripts/redeploy-with-lambda-url.sh
```

