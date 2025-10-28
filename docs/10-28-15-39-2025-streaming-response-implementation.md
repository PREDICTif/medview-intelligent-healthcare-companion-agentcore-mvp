# Streaming Response Implementation Plan for MedView Healthcare Companion

## Executive Summary
This document outlines the implementation plan for adding streaming responses to the MedView Healthcare Companion to improve user experience through real-time, progressive response delivery from AWS Bedrock.

## Current Architecture Analysis
Based on SOW requirements, the system currently uses:
- **AWS Lambda** for serverless compute
- **Amazon Bedrock** with Claude LLM for AI responses
- **AgentCore Runtime** for agent execution with built-in authentication
- **API Gateway** for REST endpoints
- **Aurora PostgreSQL** for HIPAA-compliant data storage

## Implementation Strategy

### Phase 1: WebSocket Infrastructure (Week 1)

#### Files to Create/Modify:
1. **`lambda/websocket-handlers.ts`** (NEW - Lines 1-120)
   - Connect handler: Lines 8-20
   - Disconnect handler: Lines 22-34
   - Message handler with streaming: Lines 36-120

2. **`infrastructure/cdk-stack.ts`** (NEW - Lines 1-200)
   - WebSocket API definition: Lines 45-85
   - Lambda functions: Lines 87-145
   - IAM permissions: Lines 147-165

### Phase 2: Frontend Integration (Week 1-2)

#### Files to Modify:
3. **`frontend/components/StreamingChat.tsx`** (NEW - Lines 1-210)
   - WebSocket connection management: Lines 45-85
   - Streaming message handler: Lines 87-125
   - UI rendering with progressive updates: Lines 127-210

4. **`frontend/hooks/useWebSocket.ts`** (TO CREATE)
   ```typescript
   // Lines 1-15: Connection state management
   // Lines 16-45: Reconnection logic with exponential backoff
   // Lines 46-80: Message queue handling
   ```

### Phase 3: Backend Streaming Handler (Week 2)

#### Files to Modify:
5. **`lambda/bedrock-streaming-handler.ts`** (Lines 1-55)
   - Bedrock streaming configuration: Lines 15-30
   - Chunk processing: Lines 31-45
   - Error handling: Lines 46-55

6. **`utils/stream-processor.ts`** (TO CREATE)
   ```typescript
   // Lines 1-20: Chunk parsing and validation
   // Lines 21-50: Medical terminology safety checks
   // Lines 51-80: Response formatting
   ```

### Phase 4: Fallback Mechanisms (Week 2-3)

#### Server-Sent Events (SSE) Fallback:
7. **`lambda/sse-handler.ts`** (TO CREATE)
   ```typescript
   // Lines 1-30: SSE headers configuration
   // Lines 31-60: Stream initialization
   // Lines 61-100: Chunk delivery with keep-alive
   ```

## Critical Implementation Details

### WebSocket Connection Management
**File:** `frontend/components/StreamingChat.tsx`
**Lines:** 45-85

Key features:
- Auto-reconnection with exponential backoff
- Connection state persistence in Redux/Context
- Graceful degradation to SSE

### Streaming Response Processing
**File:** `lambda/websocket-handlers.ts`
**Lines:** 36-120

Implementation requirements:
1. Enable streaming in Bedrock request (Line 50):
   ```typescript
   stream: true
   ```
2. Process chunks asynchronously (Lines 70-90)
3. Maintain conversation context (Lines 91-110)

### Healthcare-Specific Safety Features
**File:** `utils/medical-safety-checker.ts`
**Lines:** TO CREATE

Required validations:
- Emergency keyword detection
- Medication interaction warnings
- HIPAA compliance for streamed data

## Performance Optimizations

### 1. Chunk Size Configuration
**File:** `lambda/websocket-handlers.ts`
**Line:** 75
```typescript
const OPTIMAL_CHUNK_SIZE = 256; // characters
```

### 2. Connection Pooling
**File:** `infrastructure/cdk-stack.ts`
**Lines:** 180-195
- Configure Lambda reserved concurrency
- Implement connection limits per user

## Security Considerations

### Authentication Flow
**Files to Modify:**
1. **`frontend/services/auth-service.ts`** (Lines 45-60)
   - Extend existing Cognito JWT authentication for WebSocket connections
   - Add WebSocket token refresh logic
   - Reuse existing authentication tokens from AgentCore Runtime

**Note:** Leverage AgentCore's built-in Cognito JWT authorizer for consistent authentication across REST and WebSocket endpoints

### HIPAA Compliance
**Critical Files:**
- `lambda/websocket-handlers.ts` (Lines 95-110): Encrypt before storing
- `infrastructure/cdk-stack.ts` (Lines 25-30): Enable encryption at rest

## Testing Strategy

### Unit Tests Required:
1. **`__tests__/websocket-handlers.test.ts`**
   - Connection lifecycle testing
   - Message streaming validation
   - Error handling scenarios

2. **`__tests__/streaming-chat.test.tsx`**
   - UI responsiveness during streaming
   - Reconnection behavior
   - Message ordering validation

### Integration Tests:
3. **`__tests__/e2e/streaming-flow.test.ts`**
   - Full streaming pipeline
   - Fallback mechanism triggers
   - Performance under load

## Deployment Steps

### 1. Infrastructure Deployment
```bash
cd infrastructure/
cdk deploy MedViewStreamingStack --require-approval never
```

### 2. Lambda Function Updates
Deploy in order:
1. WebSocket handlers
2. SSE fallback handler
3. Update existing REST endpoints

### 3. Frontend Deployment
```bash
npm run build
aws s3 sync build/ s3://medview-frontend-bucket/
aws cloudfront create-invalidation --distribution-id ABCD1234 --paths "/*"
```

## Monitoring and Metrics

### CloudWatch Dashboards
**File:** `infrastructure/cdk-stack.ts`
**Lines:** 220-245

Key metrics to track:
- WebSocket connection count
- Average streaming latency
- Chunk delivery rate
- Error rates by type

### Alarms Configuration
**File:** `infrastructure/monitoring-stack.ts` (TO CREATE)
```typescript
// Lines 1-30: High latency alarm (>2s)
// Lines 31-50: Connection failure rate alarm (>5%)
// Lines 51-70: Bedrock throttling alarm
```

## Timeline

- **Week 1**: WebSocket infrastructure and basic streaming
- **Week 2**: Frontend integration, backend streaming handler, and testing
- **Week 3**: SSE fallback and production deployment
- **Week 4**: Monitoring setup and performance tuning

## Success Criteria

Per SOW requirements:
- Response time < 2 seconds for initial chunk
- 99.9% uptime for WebSocket connections
- Graceful degradation to SSE when WebSocket fails

## Architectural Decisions

### Why Not Feature Flags?
This implementation does not include feature flags for streaming enable/disable. Streaming will be the default and only response mode once deployed. If rollback is needed, use CDK deployment rollback rather than runtime flags.

### Authentication Strategy
Reuse existing AgentCore Runtime's Cognito JWT authorizer for WebSocket connections. No separate authentication layer needed - maintains consistency across all endpoints.

## Contact

For implementation questions, refer to:
- Technical Lead: Infrastructure team
- Frontend: React development team
- Backend: Lambda/Bedrock team

---
*Document Version: 1.1*
*Last Updated: 10-28-2025*
*Status: Ready for Implementation*
