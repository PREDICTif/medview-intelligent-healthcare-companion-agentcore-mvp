# Cognito User ID Integration

## Overview

The medical assistant agent now properly extracts and uses Cognito user IDs for personalized experiences and memory management.

## Implementation

### User ID Extraction Priority

The `extract_user_id_from_context()` function follows this priority order:

1. **`context.identity.sub`** - Cognito user ID from JWT token (PRIMARY)
2. **`context.identity.user_id`** - Alternative user ID field
3. **`context.identity.username`** - Username fallback
4. **`context.user_id`** - Direct user ID on context
5. **`user_session-{session_id}`** - Session-based fallback
6. **`default_user`** - Last resort default

### Code Location

- **Production**: `agent/strands_agent.py` (lines 70-115)
- **Local Testing**: `agent/strands_agent_local.py` (lines 70-115)

### How It Works

```python
def extract_user_id_from_context(context) -> str:
    """Extract Cognito user ID from AgentCore context"""
    
    # Try to get Cognito sub (user ID) from identity
    if hasattr(context, 'identity') and context.identity:
        # Cognito sub is the primary user identifier
        if hasattr(context.identity, 'sub') and context.identity.sub:
            cognito_user_id = context.identity.sub
            return cognito_user_id
    
    # ... fallback logic ...
```

## Benefits

### 1. **Personalized Memory**
- Each user's conversation history is stored separately
- Memory is tied to their Cognito user ID
- Conversations persist across sessions

### 2. **Patient Data Association**
- Future enhancement: Link patient records to Cognito users
- Secure access control based on user identity
- HIPAA-compliant data segregation

### 3. **Audit Trail**
- Track which user made which queries
- Monitor usage patterns per user
- Compliance and security logging

### 4. **Multi-Session Support**
- Same user can have multiple sessions
- Memory persists across devices
- Seamless experience

## Testing

### Local Testing

Run the local test version to verify user ID extraction:

```bash
python agent/strands_agent_local.py
```

This will run 5 test scenarios:
1. ✅ Cognito sub extraction
2. ✅ Identity user_id fallback
3. ✅ Username fallback
4. ✅ Session-based fallback
5. ✅ Default fallback

### Production Testing

When users log in through the web interface:
- Cognito provides JWT token with `sub` claim
- AgentCore extracts identity from token
- Agent uses `context.identity.sub` as user ID

## Deployment Status

✅ **Deployed to Production**
- Agent Runtime: `arn:aws:bedrock-agentcore:us-east-1:584360833890:runtime/strands_agent-7xbjvREebP`
- Web Interface: https://d1kg75xyopexst.cloudfront.net
- Cognito User Pool: `us-east-1_GReO412Ab`

## Usage in Code

### Memory Integration

```python
# Extract user ID from context
actor_id = extract_user_id_from_context(context)

# Create agent with memory tied to user
agent = create_agent_with_memory(
    memory_id=memory_id,
    actor_id=actor_id,  # Cognito user ID
    session_id=session_id
)
```

### Patient Database Integration

Future enhancement - associate patient records with users:

```python
# Get user's Cognito ID
user_id = extract_user_id_from_context(context)

# Query patient records for this user
patient_records = get_patient_records_for_user(user_id)
```

## Security Considerations

1. **JWT Validation**: AgentCore validates JWT tokens before passing context
2. **User Isolation**: Each user's data is isolated by their Cognito sub
3. **No PII in Logs**: User IDs are UUIDs, not personally identifiable
4. **Secure Storage**: Memory and patient data use encrypted storage

## Monitoring

Check CloudWatch logs for user ID extraction:

```
🔍 Extracting user ID from context
✅ Using Cognito user ID (sub): 12345678-1234-1234-1234-123456789abc
```

## Troubleshooting

### Issue: User ID shows as "default_user"

**Cause**: Context doesn't contain identity information

**Solution**: 
- Verify user is logged in through Cognito
- Check JWT token is being passed correctly
- Review AgentCore authentication configuration

### Issue: Different user ID each session

**Cause**: Using session-based fallback instead of Cognito sub

**Solution**:
- Ensure `context.identity.sub` is populated
- Verify Cognito JWT token includes `sub` claim
- Check AgentCore identity extraction

## Next Steps

1. **Patient Record Association**: Link Cognito users to patient records
2. **User Preferences**: Store user-specific settings
3. **Usage Analytics**: Track per-user metrics
4. **Access Control**: Implement role-based permissions

## References

- AgentCore Context Documentation
- Cognito JWT Token Structure
- Memory Integration Guide
- Patient Database Schema
