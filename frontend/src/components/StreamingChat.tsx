import { useState, useEffect, useRef } from 'react';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import PromptInput from '@cloudscape-design/components/prompt-input';
import Alert from '@cloudscape-design/components/alert';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket';
import { getAccessToken } from '../auth';

interface Message {
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface StreamingChatProps {
  webSocketUrl: string | null;
  agentRuntimeArn: string;
  region: string;
}

export default function StreamingChat({ webSocketUrl, agentRuntimeArn, region }: StreamingChatProps) {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { isConnected, isConnecting, sendMessage, lastMessage, error: wsError, reconnect } = useWebSocket(webSocketUrl);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const msg = lastMessage as WebSocketMessage;

    switch (msg.type) {
      case 'start':
        setIsProcessing(true);
        setStreamingContent('');
        break;

      case 'chunk':
        if (msg.content) {
          setStreamingContent((prev) => prev + msg.content);
        }
        break;

      case 'end':
        // Finalize streaming message
        setStreamingContent((currentContent) => {
          if (currentContent) {
            setMessages((prev) => [
              ...prev,
              {
                type: 'agent',
                content: currentContent,
                timestamp: new Date(),
              },
            ]);
          }
          return '';
        });
        setIsProcessing(false);
        break;

      case 'error':
        console.error('WebSocket error:', msg.message);
        setIsProcessing(false);
        setMessages((prev) => [
          ...prev,
          {
            type: 'agent',
            content: `Error: ${msg.message}`,
            timestamp: new Date(),
          },
        ]);
        setStreamingContent('');
        break;
    }
  }, [lastMessage]);

  const handleSubmit = async () => {
    if (!prompt.trim() || isProcessing) return;

    // Add user message
    const userMessage: Message = {
      type: 'user',
      content: prompt,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setPrompt('');

    // Get JWT token for authentication
    const jwtToken = await getAccessToken();

    // Send to WebSocket with JWT
    sendMessage({
      prompt: userMessage.content,
      agentRuntimeArn,
      region,
      jwtToken,
    });
  };

  const getConnectionStatus = () => {
    if (isConnecting) return <StatusIndicator type="pending">Connecting...</StatusIndicator>;
    if (isConnected) return <StatusIndicator type="success">Connected</StatusIndicator>;
    return <StatusIndicator type="error">Disconnected</StatusIndicator>;
  };

  return (
    <Container>
      <SpaceBetween size="m">
        <Box textAlign="right">
          {getConnectionStatus()}
          {!isConnected && !isConnecting && (
            <button onClick={reconnect}>Reconnect</button>
          )}
        </Box>

        {wsError && (
          <Alert type="error" header="Connection Error">
            {wsError}
          </Alert>
        )}

        <div style={{ maxHeight: '600px', overflowY: 'auto', padding: '16px' }}>
          <SpaceBetween size="m">
            {messages.map((message, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}
              >
                {message.type === 'agent' && <Avatar iconName="contact" />}
                
                <ChatBubble
                  type={message.type === 'user' ? 'outgoing' : 'incoming'}
                  showName={message.type === 'agent'}
                  name={message.type === 'agent' ? 'Agent' : undefined}
                >
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </ChatBubble>

                {message.type === 'user' && <Avatar iconName="user-profile" />}
              </div>
            ))}

            {/* Streaming message (in progress) */}
            {streamingContent && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'flex-start',
                  alignItems: 'flex-start',
                  gap: '12px',
                }}
              >
                <Avatar iconName="contact" />
                
                <ChatBubble
                  type="incoming"
                  showName={true}
                  name="Agent"
                >
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {streamingContent}
                    </ReactMarkdown>
                    <StatusIndicator type="in-progress">Streaming...</StatusIndicator>
                  </div>
                </ChatBubble>
              </div>
            )}

            <div ref={messagesEndRef} />
          </SpaceBetween>
        </div>

        <PromptInput
          value={prompt}
          onChange={({ detail }) => setPrompt(detail.value)}
          onAction={handleSubmit}
          placeholder="Ask a question..."
          actionButtonLabel="Send"
          actionButtonAriaLabel="Send message"
          disabled={isProcessing || !isConnected}
        />
      </SpaceBetween>
    </Container>
  );
}

