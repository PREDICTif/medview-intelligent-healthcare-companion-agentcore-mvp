# Solution: Pass User ID via Custom Header

## Problem Identified
- AgentCore validates JWT but doesn't pass claims to agent context
- `context.identity` doesn't exist
- `context.request_headers` is None
- Agent has no way to access the Cognito user ID from the JWT

## Solution: Custom Header Approach

### Step 1: Frontend - Send User ID in Custom Header

Modify `frontend/src/agentcore.ts` to include the user's Cognito sub in a custom header:

```typescript
// Get user info
const user = await getCurrentUser();
if (!user || !user.sub) {
  throw new Error('User not authenticated or missing sub claim');
}

// Send request with custom header
headers: {
  'Authorization': `Bearer ${jwtToken}`,
  'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': user.sub,  // Cognito user ID
  'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
  'X-Amzn-Trace-Id': traceId,
}
```

### Step 2: Check if AgentCore Passes Custom Headers

According to AWS documentation, AgentCore has a header allowlist feature. We need to check if custom headers are passed through.

### Alternative: Use Session ID Mapping

If custom headers don't work, we can:
1. Store a mapping of session_id → cognito_user_id in DynamoDB
2. On first request, store the mapping
3. On subsequent requests, look up the user ID from session ID

## Implementation Plan

Let's try the custom header approach first since it's simpler.
