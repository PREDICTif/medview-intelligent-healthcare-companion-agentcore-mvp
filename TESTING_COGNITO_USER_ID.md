# Testing Cognito User ID Extraction

## Quick Test Methods

### Method 1: Automated CloudWatch Log Check (Recommended)

Run the automated test script:

```bash
python test_cognito_user_id.py
```

This will:
- ✅ Check Cognito configuration
- ✅ Search CloudWatch logs for user ID extraction
- ✅ Verify memory configuration
- ✅ Show registered users
- ✅ Provide detailed results

### Method 2: Manual CloudWatch Logs Check

1. **Open AWS CloudWatch Console**
   - Go to: https://console.aws.amazon.com/cloudwatch/
   - Region: us-east-1

2. **Navigate to Log Groups**
   - Find: `/aws/bedrock-agentcore/runtime/strands_agent-7xbjvREebP`

3. **Search for User ID Logs**
   - Click "Search log group"
   - Use filter: `"Using Cognito user ID"`
   - Time range: Last 30 minutes

4. **Look for Log Entries Like:**
   ```
   🔍 Extracting user ID from context: <class 'bedrock_agentcore.context.RequestContext'>
      Found identity object: <class 'bedrock_agentcore.identity.Identity'>
   ✅ Using Cognito user ID (sub): 12345678-1234-1234-1234-123456789abc
   ```

### Method 3: Web Interface Test

1. **Open the Application**
   ```
   https://d1kg75xyopexst.cloudfront.net
   ```

2. **Sign Up / Log In**
   - Create a new account or use existing credentials
   - Cognito will assign you a unique user ID (sub)

3. **Send a Test Message**
   ```
   "Hello! Can you remember my name is John?"
   ```

4. **Log Out and Log Back In**
   - Use the same credentials

5. **Test Memory**
   ```
   "What's my name?"
   ```
   
   If the agent remembers "John", your Cognito user ID is working correctly!

### Method 4: Check Cognito Users

**List registered users:**

```bash
aws cognito-idp list-users \
  --user-pool-id us-east-1_GReO412Ab \
  --region us-east-1 \
  --query 'Users[*].[Username,Attributes[?Name==`sub`].Value|[0]]' \
  --output table
```

**Example output:**
```
-----------------------------------------
|              ListUsers                |
+----------------------+----------------+
|  john.doe@email.com  |  abc-123-def   |
|  jane.smith@email.com|  xyz-789-ghi   |
+----------------------+----------------+
```

### Method 5: Real-Time Log Streaming

**Stream logs in real-time:**

```bash
aws logs tail /aws/bedrock-agentcore/runtime/strands_agent-7xbjvREebP \
  --follow \
  --region us-east-1 \
  --filter-pattern "Cognito user ID"
```

Then use the web interface and watch for log entries.

## What to Look For

### ✅ Success Indicators

1. **In CloudWatch Logs:**
   ```
   ✅ Using Cognito user ID (sub): 12345678-1234-1234-1234-123456789abc
   ```

2. **Memory Persistence:**
   - Agent remembers previous conversations
   - Same user across sessions
   - Different users have separate memories

3. **User ID Format:**
   - UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - Consistent across sessions for same user
   - Different for each user

### ⚠️ Warning Signs

1. **Session-Based Fallback:**
   ```
   ⚠️ Using session-based ID: user_session-789
   ```
   - Means Cognito identity not found
   - User might not be logged in
   - JWT token might be missing

2. **Default User:**
   ```
   ⚠️ Using default user ID
   ```
   - No identity information available
   - Authentication might be failing

3. **No Memory Persistence:**
   - Agent doesn't remember previous conversations
   - Different user ID each session

## Troubleshooting

### Issue: No Cognito User ID in Logs

**Possible Causes:**
1. User not logged in through Cognito
2. JWT token not being passed
3. AgentCore not extracting identity

**Solutions:**
1. Verify user is logged in via web interface
2. Check browser console for authentication errors
3. Verify Cognito configuration in AgentCore

### Issue: Different User ID Each Session

**Possible Causes:**
1. Using session-based fallback
2. Cognito identity not persisting

**Solutions:**
1. Check if `context.identity.sub` is populated
2. Verify JWT token includes `sub` claim
3. Review AgentCore authentication flow

### Issue: Memory Not Working

**Possible Causes:**
1. Memory not configured
2. User ID changing between sessions
3. Memory client initialization failing

**Solutions:**
1. Check memory ID in SSM: `/app/medicalassistant/agentcore/memory_id`
2. Verify user ID is consistent in logs
3. Check memory client initialization logs

## Expected Log Flow

When a user makes a request, you should see:

```
🚀 Medical Assistant Agent invoked!
📦 Payload: {...}
🔧 Context: <RequestContext>

🔍 Extracting user ID from context: <class 'bedrock_agentcore.context.RequestContext'>
   Found identity object: <class 'bedrock_agentcore.identity.Identity'>
✅ Using Cognito user ID (sub): 12345678-1234-1234-1234-123456789abc

🧠 Memory setup: memory_id=mem-abc123, actor_id=12345678-1234-1234-1234-123456789abc, session_id=sess-456

🧠 Configuring memory: memory_id=mem-abc123, actor_id=12345678-1234-1234-1234-123456789abc, session_id=sess-456
✅ Memory hooks registered successfully
```

## Testing Checklist

- [ ] Run automated test script
- [ ] Check CloudWatch logs for Cognito user IDs
- [ ] Verify users are registered in Cognito
- [ ] Test memory persistence across sessions
- [ ] Confirm different users have separate memories
- [ ] Check user ID format is UUID
- [ ] Verify no session-based fallbacks in production

## Quick Commands

**Run automated test:**
```bash
python test_cognito_user_id.py
```

**Check recent logs:**
```bash
aws logs tail /aws/bedrock-agentcore/runtime/strands_agent-7xbjvREebP \
  --since 30m \
  --region us-east-1 \
  --filter-pattern "Cognito"
```

**List Cognito users:**
```bash
aws cognito-idp list-users \
  --user-pool-id us-east-1_GReO412Ab \
  --region us-east-1
```

**Check memory configuration:**
```bash
aws ssm get-parameter \
  --name "/app/medicalassistant/agentcore/memory_id" \
  --region us-east-1
```

## Support

If you encounter issues:
1. Run the automated test script for diagnostics
2. Check CloudWatch logs for error messages
3. Verify Cognito configuration
4. Review AgentCore authentication setup
