// Note: Using direct HTTP calls to AgentCore with JWT bearer tokens
// as shown in AWS AgentCore documentation
// AgentCore validates the client_id claim which is in Access Token, not ID Token
import { getAccessToken } from './auth';

const region = (import.meta as any).env?.VITE_REGION || 'us-east-1';
const agentRuntimeArn = (import.meta as any).env?.VITE_AGENT_RUNTIME_ARN;

// Session ID management for memory persistence
// Create a user-specific session ID that persists across browser sessions
// This allows AgentCore Memory to use the session_id as a stable user identifier
const getUserSpecificSessionId = async (): Promise<string> => {
  // Get current user to extract Cognito user ID
  const { getCurrentUser } = await import('./auth');
  const user = await getCurrentUser();
  
  if (!user || !user.sub) {
    // Fallback to temporary session if user not available
    const storageKey = 'agentcore_session_id';
    let sessionId = sessionStorage.getItem(storageKey);
    
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}_${Math.random().toString(36).substring(2, 15)}`;
      sessionStorage.setItem(storageKey, sessionId);
    }
    
    return sessionId;
  }
  
  // Create a stable session ID based on user ID
  // Format: user_<cognito_user_id>_session
  // This ensures the same user always gets the same session ID across browser sessions
  const userSessionId = `user_${user.sub}_session`;
  
  return userSessionId;
};

export interface InvokeAgentRequest {
  prompt: string;
}

export interface InvokeAgentResponse {
  response: string;
}

export const invokeAgent = async (request: InvokeAgentRequest): Promise<InvokeAgentResponse> => {
  try {
    // Check if runtime ARN is available
    if (!agentRuntimeArn) {
      throw new Error('AgentCore Runtime ARN not configured. Please check deployment.');
    }

    // Get JWT Access token from Cognito (required for AgentCore as per AWS documentation)
    // AgentCore validates the client_id claim which is present in Access Token
    const jwtToken = await getAccessToken();
    if (!jwtToken) {
      throw new Error('Not authenticated - no access token available');
    }

    // Get current user to extract Cognito user ID (sub) for memory scoping
    const { getCurrentUser } = await import('./auth');
    const user = await getCurrentUser();
    if (!user || !user.sub) {
      throw new Error('User not authenticated or missing user ID');
    }

    // URL encode the agent runtime ARN for the API call (as per AWS documentation)
    const encodedAgentRuntimeArn = encodeURIComponent(agentRuntimeArn);
    
    // Use the correct AgentCore endpoint format from AWS documentation
    const url = `https://bedrock-agentcore.${region}.amazonaws.com/runtimes/${encodedAgentRuntimeArn}/invocations?qualifier=DEFAULT`;
    
    // Get user-specific session ID (stable across browser sessions)
    const sessionId = await getUserSpecificSessionId();
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`,
        'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': user.sub,  // Pass Cognito user ID for memory scoping
        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,  // Use persistent session ID
        'X-Amzn-Trace-Id': `trace-${Date.now()}`,
      },
      body: JSON.stringify({
        prompt: request.prompt,
        stream: true  // Enable streaming
      }),
    });
    
    console.log('AgentCore response status:', response.status);
    console.log('AgentCore response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('AgentCore error response:', errorText);
      throw new Error(`AgentCore invocation failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    let data;
    try {
      data = await response.json();
      console.log('AgentCore response data:', data);
    } catch (parseError) {
      console.error('Failed to parse JSON response:', parseError);
      const textResponse = await response.text();
      console.log('Raw response text:', textResponse);
      throw new Error(`Invalid JSON response from AgentCore: ${textResponse}`);
    }
    
    // Handle different response formats from AgentCore
    let responseText = '';
    if (typeof data === 'string') {
      responseText = data;
    } else if (data && typeof data === 'object') {
      responseText = data.response || data.content || data.text || data.message || data.output || JSON.stringify(data);
    } else {
      responseText = 'No response from agent';
    }
    
    console.log('Final response text:', responseText);
    
    return {
      response: responseText
    };

  } catch (error: any) {
    console.error('AgentCore invocation error:', error);
    throw new Error(`Failed to invoke agent: ${error.message}`);
  }
};

// Real streaming function using AgentCore's streaming API
export const invokeAgentStream = async (
  request: InvokeAgentRequest,
  onChunk: (chunk: string) => void,
  onComplete: (fullResponse: string) => void,
  onError: (error: Error) => void
): Promise<void> => {
  try {
    // Check if runtime ARN is available
    if (!agentRuntimeArn) {
      throw new Error('AgentCore Runtime ARN not configured. Please check deployment.');
    }

    // Get JWT Access token from Cognito
    // AgentCore validates the client_id claim which is present in Access Token
    const jwtToken = await getAccessToken();
    if (!jwtToken) {
      throw new Error('Not authenticated - no access token available');
    }

    // Get current user to extract Cognito user ID (sub) for memory scoping
    const { getCurrentUser } = await import('./auth');
    const user = await getCurrentUser();
    if (!user || !user.sub) {
      throw new Error('User not authenticated or missing user ID');
    }

    // URL encode the agent runtime ARN for the API call
    const encodedAgentRuntimeArn = encodeURIComponent(agentRuntimeArn);
    
    // Use the correct AgentCore endpoint format
    const url = `https://bedrock-agentcore.${region}.amazonaws.com/runtimes/${encodedAgentRuntimeArn}/invocations?qualifier=DEFAULT`;
    
    // Get user-specific session ID (stable across browser sessions)
    const sessionId = await getUserSpecificSessionId();
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`,
        'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': user.sub,  // Pass Cognito user ID for memory scoping
        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,  // Use persistent session ID
        'X-Amzn-Trace-Id': `trace-${Date.now()}`,
        'Accept': 'text/plain',  // Accept streaming response
      },
      body: JSON.stringify({
        prompt: request.prompt,
        stream: true  // Enable streaming
      }),
    });
    
    console.log('AgentCore streaming response status:', response.status);
    console.log('AgentCore streaming response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('AgentCore error response:', errorText);
      throw new Error(`AgentCore invocation failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    // Handle streaming response
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    if (reader) {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          console.log('Received chunk:', chunk);
          
          // Handle Server-Sent Events format
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // Remove 'data: ' prefix
              
              if (data.trim() && data !== '[DONE]') {
                try {
                  const parsed = JSON.parse(data);
                  console.log('Parsed event:', JSON.stringify(parsed, null, 2));
                  
                  // Add specific logging for web search responses
                  if (parsed.event && parsed.event.contentBlockStart && parsed.event.contentBlockStart.start && parsed.event.contentBlockStart.start.toolUse) {
                    const toolUse = parsed.event.contentBlockStart.start.toolUse;
                    console.log('Tool use detected:', toolUse.name);
                    if (toolUse.name === 'web_search') {
                      console.log('Web search tool called with input:', toolUse.input);
                    }
                  }
                  
                  // Handle different Strands event types
                  if (parsed.event) {
                    const event = parsed.event;
                    
                    // Handle content block delta (actual text content)
                    if (event.contentBlockDelta && event.contentBlockDelta.delta && event.contentBlockDelta.delta.text) {
                      const text = event.contentBlockDelta.delta.text;
                      fullResponse += text;
                      onChunk(text);
                    }
                    // Handle message delta (streaming text)
                    else if (event.messageDelta && event.messageDelta.delta && event.messageDelta.delta.text) {
                      const text = event.messageDelta.delta.text;
                      fullResponse += text;
                      onChunk(text);
                    }
                    // Handle message stop (final message)
                    else if (event.messageStop && event.messageStop.message) {
                      const message = event.messageStop.message;
                      if (message.content && Array.isArray(message.content)) {
                        for (const content of message.content) {
                          if (content.text) {
                            // For complete responses (like tool results), show the full text
                            const text = content.text;
                            if (!fullResponse.trim()) {
                              // If we haven't received any chunks yet, this is the complete response
                              fullResponse = text;
                              // Simulate streaming by chunking the response
                              const words = text.split(' ');
                              const chunkSize = 5;
                              let currentIndex = 0;
                              
                              const streamWords = () => {
                                if (currentIndex >= words.length) return;
                                
                                const chunk = words.slice(currentIndex, currentIndex + chunkSize).join(' ');
                                const isLastChunk = currentIndex + chunkSize >= words.length;
                                const chunkToSend = isLastChunk ? chunk : chunk + ' ';
                                
                                onChunk(chunkToSend);
                                currentIndex += chunkSize;
                                
                                if (currentIndex < words.length) {
                                  setTimeout(streamWords, 30);
                                }
                              };
                              
                              streamWords();
                            } else {
                              // We already have content, just add this
                              fullResponse += text;
                              onChunk(text);
                            }
                          }
                        }
                      }
                    }
                    // Handle tool use results
                    else if (event.contentBlockStop && event.contentBlockStop.contentBlockIndex !== undefined) {
                      console.log('Tool use completed:', event.contentBlockStop);
                    }
                    // Handle tool result content
                    else if (event.contentBlockStart && event.contentBlockStart.start && event.contentBlockStart.start.text) {
                      const text = event.contentBlockStart.start.text;
                      fullResponse += text;
                      onChunk(text);
                    }
                    // Handle message content
                    else if (event.messageStart && event.messageStart.message && event.messageStart.message.content) {
                      const content = event.messageStart.message.content;
                      if (Array.isArray(content) && content[0] && content[0].text) {
                        const text = content[0].text;
                        fullResponse += text;
                        onChunk(text);
                      }
                    }
                  }
                  // Handle direct text content
                  else if (parsed.text) {
                    const text = parsed.text;
                    fullResponse += text;
                    onChunk(text);
                  }
                  // Handle result format (complete response)
                  else if (parsed.result && parsed.result.message) {
                    const message = parsed.result.message;
                    let responseText = '';
                    
                    if (typeof message === 'string') {
                      responseText = message;
                    } else if (message.content && Array.isArray(message.content) && message.content[0] && message.content[0].text) {
                      responseText = message.content[0].text;
                    }
                    
                    if (responseText) {
                      fullResponse = responseText;
                      // Simulate streaming for complete responses
                      const words = responseText.split(' ');
                      const chunkSize = 5;
                      let currentIndex = 0;
                      
                      const streamWords = () => {
                        if (currentIndex >= words.length) return;
                        
                        const chunk = words.slice(currentIndex, currentIndex + chunkSize).join(' ');
                        const isLastChunk = currentIndex + chunkSize >= words.length;
                        const chunkToSend = isLastChunk ? chunk : chunk + ' ';
                        
                        onChunk(chunkToSend);
                        currentIndex += chunkSize;
                        
                        if (currentIndex < words.length) {
                          setTimeout(streamWords, 30);
                        }
                      };
                      
                      streamWords();
                    }
                  }
                } catch (parseError) {
                  console.log('Failed to parse JSON, treating as text:', data);
                  // If not JSON, treat as plain text (but skip control messages)
                  if (data.trim() && !data.includes('init_event_loop') && !data.includes('start_event_loop')) {
                    fullResponse += data;
                    onChunk(data);
                  }
                }
              }
            }
            // Handle non-SSE lines (fallback)
            else if (line.trim() && !line.includes('init_event_loop') && !line.includes('start_event_loop')) {
              try {
                const parsed = JSON.parse(line);
                if (parsed.text) {
                  fullResponse += parsed.text;
                  onChunk(parsed.text);
                }
              } catch {
                // Treat as plain text if not JSON
                fullResponse += line;
                onChunk(line);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }

    console.log('Streaming complete. Full response:', fullResponse);
    onComplete(fullResponse);

  } catch (error: any) {
    console.error('AgentCore streaming error:', error);
    onError(error);
  }
};