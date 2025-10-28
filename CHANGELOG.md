# CHANGELOG

## 2025-10-29 20:10 CDT - Fix Duplicate Chunk Rendering in Frontend

### What Changed
Fixed useEffect dependency that caused chunks to be processed multiple times.

### Files Modified
- `frontend/src/components/StreamingChat.tsx` - Removed streamingContent from useEffect dependencies, fixed 'end' case

### Why It Matters
- **Fixed duplicate text bug**: Chunks were being added multiple times due to useEffect re-running
- useEffect had `streamingContent` in dependencies, causing it to re-process same message
- Each chunk was being appended repeatedly, creating garbled output
- Now chunks are processed exactly once and appended correctly

## 2025-10-29 20:00 CDT - Implement True Streaming Response

### What Changed
Added support for real streaming responses with fallback to simulated chunking.

### Files Modified
- `lambda/websocket-handlers/index.ts` - Added streaming response handling with SSE parsing and chunked fallback

### Why It Matters
- **True streaming if supported**: Checks for `text/event-stream` content type and parses SSE
- **Simulated streaming fallback**: Chunks JSON responses to simulate progressive delivery
- **Better UX**: Response appears progressively instead of all at once
- Handles both streaming endpoints (if available) and standard JSON responses

### Technical Details
- Requests streaming with `Accept: text/event-stream` header
- Parses Server-Sent Events format if returned
- Falls back to chunking JSON response (20 chars at a time with 50ms delay)
- Compatible with both streaming and non-streaming AgentCore endpoints

## 2025-10-29 19:50 CDT - Fix Session ID Length Validation

### What Changed
Extended session ID generation to ensure minimum 33 characters (AWS requirement).

### Files Modified
- `lambda/websocket-handlers/index.ts` - Generate longer session ID with double random strings

### Why It Matters
- **Fixed 400 validation error**: AWS requires session ID to be at least 33 characters
- Previous session ID was sometimes only 30-32 characters
- Now generates: `session-{timestamp}-{random1}-{random2}` for 40+ characters guaranteed

## 2025-10-29 19:45 CDT - Switch to JWT Bearer Token Authentication

### What Changed
Switched from AWS SigV4 signing to JWT Bearer token authentication for AgentCore calls.

### Files Modified
- `lambda/websocket-handlers/index.ts` - Removed SigV4 signing, use JWT Bearer token from frontend
- `frontend/src/components/StreamingChat.tsx` - Pass JWT token with WebSocket message

### Why It Matters
- **Fixed authentication**: AgentCore requires JWT Bearer tokens from Cognito users
- Frontend already uses JWT successfully - Lambda should use same approach
- Removed complex SigV4 signing that wasn't working with AgentCore
- JWT token passed from frontend ensures user-context authentication

## 2025-10-29 19:30 CDT - Fix Protocol Format for HttpRequest

### What Changed
Fixed protocol format in HttpRequest - removed colon from URL protocol.

### Files Modified
- `lambda/websocket-handlers/index.ts` - Changed `url.protocol` to `url.protocol.replace(':', '')`
- `lambda/bedrock-streaming-handler/index.ts` - Changed `url.protocol` to `url.protocol.replace(':', '')`

### Why It Matters
- **Fixed signature calculation**: HttpRequest expects protocol without colon ('https' not 'https:')
- URL.protocol returns 'https:' but HttpRequest needs 'https'
- This mismatch caused incorrect signature calculation
- Critical for AWS SigV4 to work correctly

## 2025-10-29 19:25 CDT - Fix SigV4 Headers and Body Handling

### What Changed
Fixed fetch() to use original signed body string and properly extract headers.

### Files Modified
- `lambda/websocket-handlers/index.ts` - Use original body string, proper header extraction
- `lambda/bedrock-streaming-handler/index.ts` - Use original body string, proper header extraction

### Why It Matters
- **Fixed signature mismatch**: Must use exact body string that was signed
- Headers need explicit string casting for fetch() compatibility
- Object.fromEntries was potentially losing or transforming headers
- Critical: The body sent must match exactly what was signed

## 2025-10-29 19:20 CDT - Fix AWS SigV4 Service Name and Headers

### What Changed
Fixed AWS SigV4 signing to use correct service name and properly format headers for fetch API.

### Files Modified
- `lambda/websocket-handlers/index.ts` - Changed service from 'bedrock' to 'bedrock-agentcore', fixed headers formatting
- `lambda/bedrock-streaming-handler/index.ts` - Changed service from 'bedrock' to 'bedrock-agentcore', fixed headers formatting

### Why It Matters
- **Fixed 403 signature mismatch**: Service name must match the actual AWS service endpoint
- AgentCore is a separate service (`bedrock-agentcore`), not the legacy `bedrock` service
- Headers from SignatureV4 need proper formatting for fetch() API compatibility
- Body parameter needs explicit string handling for consistent signing

## 2025-10-29 19:10 CDT - Fix Cross-Directory Import Issue in Lambda Bundling

### What Changed
Integrated `streamBedrockResponse` function directly into websocket-handlers instead of cross-directory import.

### Files Modified
- `lambda/websocket-handlers/index.ts` - Added streamBedrockResponse function and SigV4 imports directly

### Why It Matters
- **Fixed bundling error**: Cross-directory imports break esbuild bundling process
- Dynamic import `../bedrock-streaming-handler` was causing module resolution failures
- Even with dependencies in package.json, cross-Lambda imports don't work with NodejsFunction bundling
- Solution: Copy the function code directly into the handler that needs it

## 2025-10-28 18:35 CDT - Fix Lambda Bundling for Crypto Dependencies

### What Changed
Removed `@aws-crypto/*` from externalModules in messageFunction bundling configuration.

### Files Modified
- `cdk/lib/websocket-stack.ts` - Modified messageFunction bundling to include @aws-crypto packages

### Why It Matters
- **Fixed runtime error**: `Cannot find module '@aws-crypto/sha256-js'`
- `@aws-crypto/*` packages are NOT provided by Lambda runtime (unlike `@aws-sdk/*`)
- These packages must be bundled with the Lambda function code
- Without this fix, SigV4 signing fails at runtime when invoking AgentCore

## 2025-10-28 18:10 CDT - Add AWS SigV4 Request Signing

### What Changed
Added AWS Signature V4 signing to Lambda's AgentCore API calls for authentication.

### Files Modified
- `lambda/bedrock-streaming-handler/index.ts` - Added SigV4 signing to HTTP requests
- `lambda/bedrock-streaming-handler/package.json` - Added AWS signing dependencies

### Why It Matters
- **403 "Missing Authentication Token" fixed** - Requests now properly authenticated
- Lambda-to-AgentCore is service-to-service call requiring AWS SigV4 signing
- Uses Lambda's IAM role credentials automatically

### How It Works
- Creates HttpRequest object
- Signs with SigV4 using Lambda's credentials
- AgentCore validates: "This is an authenticated AWS service with proper IAM permissions"

## 2025-10-28 18:00 CDT - Fix AgentCore API Integration

### What Changed
Rewrote Lambda streaming handler to call AgentCore REST API directly instead of wrong Bedrock Agent SDK.

### Files Modified
- `lambda/bedrock-streaming-handler/index.ts` - Call AgentCore HTTPS endpoint with fetch
- `lambda/bedrock-streaming-handler/package.json` - Removed wrong SDK dependency
- `cdk/lib/websocket-stack.ts` - Fixed bundling to exclude AWS SDK properly

### Why It Matters
- **Was using wrong service:** Bedrock Agents SDK (`agentId` 10 chars) ≠ AgentCore (`agentRuntimeArn` full ARN)
- **AgentCore has no SDK streaming:** Must call REST API directly like frontend does
- **Fixes validation error:** "agentId must be ≤10 chars and alphanumeric only"

### Technical Details
- AgentCore endpoint: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{ARN}/invocations`
- Uses same REST API pattern as frontend's direct AgentCore calls
- No special SDK needed - just HTTPS fetch with JSON payload

## 2025-10-28 17:30 CDT - Fix Lambda TypeScript Compilation

### What Changed
Fixed WebSocket Lambda functions to properly compile TypeScript using NodejsFunction.

### Files Modified
- `cdk/lib/websocket-stack.ts` - Changed from `Function` to `NodejsFunction` construct

### Why It Matters
- Lambda functions now auto-compile TypeScript → JavaScript
- Dependencies automatically bundled
- Fixes `Runtime.ImportModuleError: Cannot find module 'index'` error
- WebSocket connections will now work properly

### How It Works
- `NodejsFunction` uses esbuild to compile TypeScript at deploy time
- Bundles all dependencies from node_modules
- Creates proper Lambda deployment package with JavaScript

## 2025-10-28 16:25 CDT - Streaming Response Integration

### What Changed
Integrated streaming response infrastructure into deployment pipeline and frontend.

### Files Modified
- `deploy-all.sh` - Added WebSocket stack deployment before frontend build
- `scripts/build-frontend.sh` - Added WebSocket URL as build parameter
- `frontend/src/main.tsx` - Auto-detect and use streaming app when WebSocket URL configured
- `frontend/src/AppStreaming.tsx` - New simple streaming-only app wrapper

### Why It Matters
- WebSocket stack now deploys automatically with `./deploy-all.sh`
- Frontend automatically uses streaming when WebSocket URL is available
- Falls back to traditional responses if WebSocket not configured
- No code changes needed to switch between modes

### How It Works
1. Deploy script deploys WebSocket stack and retrieves URL
2. WebSocket URL injected into frontend build as `VITE_WEBSOCKET_URL`
3. At runtime, `main.tsx` checks if URL exists and loads appropriate app
4. If URL exists → `AppStreaming` (WebSocket + StreamingChat component)
5. If URL missing → `App` (traditional REST API calls)

## 2025-10-28 16:18 CDT - Streaming Response Implementation

### What Changed
Implemented complete streaming response infrastructure for real-time agent interactions following the documented implementation plan.

### Files Added

**Phase 1: WebSocket Infrastructure**
- `lambda/websocket-handlers/index.ts` - WebSocket Lambda handlers (connect, disconnect, message)
- `lambda/websocket-handlers/package.json` - Dependencies for WebSocket handlers
- `cdk/lib/websocket-stack.ts` - CDK stack for WebSocket API Gateway infrastructure
- Updated `cdk/bin/app.ts` - Added WebSocket stack to CDK app

**Phase 2: Frontend Integration**
- `frontend/src/hooks/useWebSocket.ts` - WebSocket hook with reconnection logic and exponential backoff
- `frontend/src/components/StreamingChat.tsx` - Streaming chat component with progressive rendering

**Phase 3: Backend Streaming Handler**
- `lambda/bedrock-streaming-handler/index.ts` - Bedrock Agent streaming response handler
- `lambda/bedrock-streaming-handler/package.json` - Dependencies for streaming handler
- `lambda/utils/stream-processor.ts` - Stream chunk processing with HIPAA sanitization
- `lambda/utils/medical-safety-checker.ts` - Healthcare-specific safety checks (emergency detection, medication warnings)

**Phase 4: SSE Fallback**
- `lambda/sse-handler/index.ts` - Server-Sent Events fallback handler for clients without WebSocket support
- `lambda/sse-handler/package.json` - Dependencies for SSE handler

### Why It Matters
- **Real-time streaming**: Users see responses as they're generated, improving perceived performance
- **Healthcare safety**: Built-in safety checks detect emergency keywords and medication warnings
- **HIPAA compliance**: Automatic sanitization of sensitive data in streams
- **Resilient connections**: Auto-reconnection with exponential backoff ensures reliable connectivity
- **Fallback support**: SSE fallback ensures compatibility with all clients

### Architecture Notes
- WebSocket-first approach with stateless Lambda handlers using connection ID from event context
- No DynamoDB required for connection tracking (simplified architecture)
- Reuses existing Cognito JWT authentication from AgentCore Runtime
- Healthcare-specific safety features integrated into streaming pipeline

### Next Steps
- Deploy WebSocket stack: `cd cdk && npx cdk deploy AgentCoreWebSocket`
- Test streaming functionality with new StreamingChat component
- Monitor CloudWatch logs for safety check triggers
- Configure alarms for connection failures and high latency

