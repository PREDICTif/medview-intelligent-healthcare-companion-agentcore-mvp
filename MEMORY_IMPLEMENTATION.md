# AgentCore Memory Implementation

## Overview
This application uses Amazon Bedrock AgentCore Memory to persist conversation history across browser sessions. Memory is scoped per user using their Cognito user ID.

## How It Works

### 1. User Authentication
- Users sign in via Cognito
- Frontend receives JWT token with user's Cognito ID (`sub` claim)

### 2. Session ID Generation
- Frontend extracts Cognito user ID from JWT token
- Creates user-specific session ID: `user_<cognito_user_id>_session`
- This session ID is sent to AgentCore with each request

### 3. Memory Scoping
- Agent extracts user ID from the session ID format
- Uses user ID as `actor_id` for AgentCore Memory
- Memory persists across all sessions for the same user

### 4. Conversation Persistence
- `AgentCoreMemorySessionManager` automatically saves conversation history
- Previous conversations are loaded when user starts a new session
- Memory is scoped by `actor_id` (user ID) and `session_id`

## Key Files

### Frontend
- **`frontend/src/agentcore.ts`**
  - `getUserSpecificSessionId()`: Creates user-specific session ID
  - Sends session ID in `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` header

### Agent
- **`agent/strands_agent.py`**
  - `extract_user_id_from_context()`: Extracts user ID from session ID
  - `create_agent_with_memory()`: Configures `AgentCoreMemorySessionManager`
  - Uses stable user ID as `actor_id` for memory persistence

## Configuration

### Memory ID
Stored in SSM Parameter: `/app/medicalassistant/agentcore/memory_id`

### Session Manager
```python
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,
    session_id=session_id,  # user_<cognito_user_id>_session
    actor_id=actor_id        # cognito_user_id (stable across sessions)
)

session_manager = AgentCoreMemorySessionManager(
    agentcore_memory_config=memory_config,
    region_name="us-east-1"
)
```

## Testing Memory Persistence

1. **First Session**: Send "My name is Alice and I love hiking"
2. **Close Browser**: Completely close the browser
3. **New Session**: Open browser, sign in, send "What is my name?"
4. **Expected**: Agent remembers "Alice" and "hiking"

## Troubleshooting

### Memory Not Persisting
Check that:
1. User is authenticated (has valid Cognito session)
2. Session ID format is correct: `user_<uuid>_session`
3. Memory ID is configured in SSM
4. AgentCore Memory is properly initialized

### Check Logs
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/<runtime-name> \
  --since 5m --format short --region us-east-1
```

Look for:
- Session ID format
- Actor ID extraction
- Memory configuration success

## References
- [Strands AgentCore Memory Integration](https://strandsagents.com/latest/documentation/docs/community/session-managers/agentcore-memory/)
- [AgentCore Memory Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
