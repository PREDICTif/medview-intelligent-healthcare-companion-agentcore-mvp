import { SignatureV4 } from '@aws-sdk/signature-v4';
import { HttpRequest } from '@aws-sdk/protocol-http';
import { Sha256 } from '@aws-crypto/sha256-js';
import { defaultProvider } from '@aws-sdk/credential-provider-node';

/**
 * Stream responses from AgentCore by calling REST API with AWS SigV4 signing
 */
export async function streamBedrockResponse(
  prompt: string,
  agentRuntimeArn: string,
  region: string,
  onChunk: (chunk: string) => Promise<void>
): Promise<void> {
  const encodedArn = encodeURIComponent(agentRuntimeArn);
  const url = new URL(`https://bedrock-agentcore.${region}.amazonaws.com/runtimes/${encodedArn}/invocations?qualifier=DEFAULT`);
  const body = JSON.stringify({ prompt });

  try {
    // Create HTTP request for signing
    const request = new HttpRequest({
      method: 'POST',
      protocol: url.protocol.replace(':', ''), // Remove colon from protocol
      hostname: url.hostname,
      path: url.pathname + url.search,
      headers: {
        'Content-Type': 'application/json',
        'host': url.hostname,
      },
      body,
    });

    // Sign request with AWS SigV4
    const signer = new SignatureV4({
      credentials: defaultProvider(),
      region,
      service: 'bedrock-agentcore',
      sha256: Sha256,
    });

    const signedRequest = await signer.sign(request);

    // Make signed request - properly extract headers for fetch
    const headers: Record<string, string> = {};
    for (const [key, value] of Object.entries(signedRequest.headers)) {
      headers[key] = value as string;
    }

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers,
      body, // Use original body string that was signed
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`AgentCore invocation failed: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const responseText = typeof data === 'string' ? data : 
                        data.response || data.content || data.output || JSON.stringify(data);
    
    await onChunk(responseText);
    
  } catch (error) {
    console.error('Error calling AgentCore:', error);
    throw error;
  }
}

