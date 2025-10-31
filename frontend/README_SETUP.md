# Frontend Setup Guide

## Environment Variables Configuration

To fix the "Lambda function URL not configured" error, you need to set up your environment variables.

### Step 1: Deploy the CDK Stack

First, deploy or update your CDK stack to create the Lambda Function URL:

```bash
cd cdk
npm install
cdk deploy
```

After deployment, you'll see outputs including `DatabaseLambdaFunctionUrl`. **Copy this URL**.

### Step 2: Create Environment File

1. Copy the example environment file:
```bash
cd frontend
cp .env.example .env.local
```

2. Edit `.env.local` and fill in your values:

```env
# Cognito Configuration (from your AWS Cognito User Pool)
VITE_USER_POOL_ID=us-east-1_XXXXXXXXX
VITE_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Lambda Function URL (from CDK deployment output)
VITE_LAMBDA_FUNCTION_URL=https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.lambda-url.us-east-1.on.aws/
```

### Step 3: Finding Your Values

#### Cognito User Pool ID and Client ID

Run this command or check your existing deployment:
```bash
aws cognito-idp list-user-pools --max-results 10
```

Or check the AWS Console:
- Navigate to: AWS Console → Cognito → User Pools
- Click on your user pool
- Copy the **Pool Id** (format: `us-east-1_XXXXXXXXX`)
- Go to "App integration" tab → "App clients"
- Copy the **Client ID**

#### Lambda Function URL

After deploying the CDK stack, look for the output:
```bash
cd cdk
cdk deploy --outputs-file outputs.json
```

Then check `outputs.json` for `DatabaseLambdaFunctionUrl`, or run:
```bash
aws cloudformation describe-stacks --stack-name MihcStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseLambdaFunctionUrl`].OutputValue' \
  --output text
```

### Step 4: Restart Development Server

After configuring the `.env.local` file:

```bash
npm run dev
```

### Step 5: Test Patient Registration

1. Navigate to http://localhost:5173 (or your dev server URL)
2. Sign in with your Cognito credentials
3. Click "Register Patient" in the side navigation
4. Fill out the form and submit

## Troubleshooting

### Error: "Lambda function URL not configured"
- Verify `.env.local` file exists in the `frontend` directory
- Check that `VITE_LAMBDA_FUNCTION_URL` is set correctly
- Restart the dev server after changing environment variables

### Error: "Network Error" or "CORS Error"
- Verify the Lambda Function URL is correct
- Check that CORS is properly configured in the CDK stack
- Ensure the Lambda function is deployed

### Error: "Not authenticated"
- Make sure you're signed in with Cognito
- Check that `VITE_USER_POOL_ID` and `VITE_USER_POOL_CLIENT_ID` are correct
- Try signing out and signing in again

### Error: Database connection issues in Lambda
- Verify the Lambda has proper VPC configuration
- Check security groups allow Lambda → RDS communication
- Confirm RDS Data API is enabled on the Aurora cluster

## Security Note

⚠️ **IMPORTANT**: The current configuration uses `authType: NONE` on the Lambda Function URL for development convenience. For production:

1. Change to `authType: AWS_IAM` in `cdk/lib/mihc-stack.ts`
2. Implement proper authorization using AWS Cognito Identity Pool
3. Restrict CORS `allowedOrigins` to your specific domain
4. Add input validation and rate limiting

## Production Deployment

For production, consider:
1. Using API Gateway with Cognito Authorizer instead of Lambda Function URL
2. Implementing proper authentication/authorization
3. Adding WAF (Web Application Firewall)
4. Using CloudFront for the frontend
5. Restricting CORS to your domain only

