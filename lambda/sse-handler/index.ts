import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

/**
 * SSE (Server-Sent Events) Handler
 * Fallback for clients that don't support WebSocket
 */

// SSE headers configuration
function getSSEHeaders(): Record<string, string> {
  return {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  };
}

// Format SSE message
function formatSSEMessage(event: string, data: any): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

// Send keep-alive ping
function sendKeepAlive(): string {
  return `: keep-alive\n\n`;
}

/**
 * SSE stream handler
 * Streams Bedrock responses using Server-Sent Events
 */
export const sseHandler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  try {
    const body = JSON.parse(event.body || '{}');
    const { prompt, agentRuntimeArn, region } = body;

    if (!prompt) {
      return {
        statusCode: 400,
        headers: getSSEHeaders(),
        body: formatSSEMessage('error', { message: 'Prompt is required' }),
      };
    }

    // Initialize SSE stream
    let streamData = '';

    // Send initial connection message
    streamData += formatSSEMessage('connected', { message: 'Stream initialized' });

    // Send start event
    streamData += formatSSEMessage('start', { message: 'Processing request...' });

    // Import streaming handler
    const { streamBedrockResponse } = await import('../bedrock-streaming-handler');

    // Stream response chunks
    await streamBedrockResponse(
      prompt,
      agentRuntimeArn,
      region,
      async (chunk: string) => {
        streamData += formatSSEMessage('chunk', { content: chunk });
        
        // Send keep-alive every 10 chunks
        if (Math.random() < 0.1) {
          streamData += sendKeepAlive();
        }
      }
    );

    // Send completion event
    streamData += formatSSEMessage('end', { message: 'Stream complete' });

    return {
      statusCode: 200,
      headers: getSSEHeaders(),
      body: streamData,
    };
  } catch (error) {
    console.error('SSE handler error:', error);
    
    return {
      statusCode: 500,
      headers: getSSEHeaders(),
      body: formatSSEMessage('error', {
        message: error instanceof Error ? error.message : 'Internal server error',
      }),
    };
  }
};

/**
 * Health check endpoint for SSE
 */
export const healthCheck = async (): Promise<APIGatewayProxyResult> => {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify({
      status: 'healthy',
      service: 'sse-streaming',
      timestamp: new Date().toISOString(),
    }),
  };
};

