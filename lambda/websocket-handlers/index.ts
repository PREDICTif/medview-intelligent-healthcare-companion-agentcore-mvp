import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { ApiGatewayManagementApiClient, PostToConnectionCommand } from '@aws-sdk/client-apigatewaymanagementapi';

const OPTIMAL_CHUNK_SIZE = 256;

// Connect handler
export const connectHandler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  console.log('WebSocket connected:', event.requestContext.connectionId);
  
  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Connected' }),
  };
};

// Disconnect handler
export const disconnectHandler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  console.log('WebSocket disconnected:', event.requestContext.connectionId);
  
  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Disconnected' }),
  };
};

// Message handler with streaming
export const messageHandler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const connectionId = event.requestContext.connectionId!;
  const domain = event.requestContext.domainName!;
  const stage = event.requestContext.stage!;
  
  const apiGwClient = new ApiGatewayManagementApiClient({
    endpoint: `https://${domain}/${stage}`,
  });

  try {
    const body = JSON.parse(event.body || '{}');
    const { prompt, agentRuntimeArn, region, jwtToken } = body;

    if (!prompt) {
      await sendToConnection(apiGwClient, connectionId, {
        type: 'error',
        message: 'Prompt is required',
      });
      return { statusCode: 400, body: 'Prompt required' };
    }

    if (!jwtToken) {
      await sendToConnection(apiGwClient, connectionId, {
        type: 'error',
        message: 'JWT token is required',
      });
      return { statusCode: 400, body: 'JWT token required' };
    }

    // Send acknowledgment
    await sendToConnection(apiGwClient, connectionId, {
      type: 'start',
      message: 'Processing your request...',
    });

    // Stream response using integrated function
    await streamBedrockResponse(
      prompt,
      agentRuntimeArn,
      region,
      jwtToken,
      async (chunk: string) => {
        await sendToConnection(apiGwClient, connectionId, {
          type: 'chunk',
          content: chunk,
        });
      }
    );

    // Send completion
    await sendToConnection(apiGwClient, connectionId, {
      type: 'end',
      message: 'Stream complete',
    });

    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Message processed' }),
    };
  } catch (error) {
    console.error('Error processing message:', error);
    
    try {
      await sendToConnection(apiGwClient, connectionId, {
        type: 'error',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } catch (sendError) {
      console.error('Error sending error message:', sendError);
    }

    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal server error' }),
    };
  }
};

// Helper function to send messages to WebSocket connection
async function sendToConnection(
  client: ApiGatewayManagementApiClient,
  connectionId: string,
  data: any
): Promise<void> {
  const command = new PostToConnectionCommand({
    ConnectionId: connectionId,
    Data: Buffer.from(JSON.stringify(data)),
  });

  await client.send(command);
}

/**
 * Stream responses from AgentCore using JWT Bearer token authentication
 */
async function streamBedrockResponse(
  prompt: string,
  agentRuntimeArn: string,
  region: string,
  jwtToken: string,
  onChunk: (chunk: string) => Promise<void>
): Promise<void> {
  const encodedArn = encodeURIComponent(agentRuntimeArn);
  const url = `https://bedrock-agentcore.${region}.amazonaws.com/runtimes/${encodedArn}/invocations?qualifier=DEFAULT`;
  
  try {
    // Generate session ID with minimum 33 characters (AWS requirement)
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2)}-${Math.random().toString(36).substring(2)}`;
    
    // Try streaming endpoint first
    const streamingUrl = url.replace('/invocations', '/invocations-stream');
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`,
        'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': sessionId,
        'X-Amzn-Trace-Id': `trace-${Date.now()}`,
        'Accept': 'text/event-stream',  // Request streaming response
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`AgentCore invocation failed: ${response.status} - ${errorText}`);
    }

    // Check if response is streaming
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('event-stream')) {
      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const chunk = line.slice(6);
              if (chunk && chunk !== '[DONE]') {
                await onChunk(chunk);
              }
            }
          }
        }
      }
    } else {
      // Fallback to JSON response (simulate streaming by chunking)
      const data = await response.json();
      const responseText = typeof data === 'string' ? data : 
                          data.response || data.content || data.output || JSON.stringify(data);
      
      // Simulate streaming by sending chunks
      const chunkSize = 20; // characters per chunk
      for (let i = 0; i < responseText.length; i += chunkSize) {
        const chunk = responseText.slice(i, i + chunkSize);
        await onChunk(chunk);
        // Small delay to simulate streaming
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }
    
  } catch (error) {
    console.error('Error calling AgentCore:', error);
    throw error;
  }
}

