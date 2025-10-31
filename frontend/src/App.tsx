import { useState, useEffect } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import SideNavigation from '@cloudscape-design/components/side-navigation';
import ContentLayout from '@cloudscape-design/components/content-layout';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import ButtonGroup from '@cloudscape-design/components/button-group';
import Grid from '@cloudscape-design/components/grid';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import SupportPromptGroup from '@cloudscape-design/chat-components/support-prompt-group';
import PromptInput from '@cloudscape-design/components/prompt-input';
import Alert from '@cloudscape-design/components/alert';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import AuthModal from './AuthModal';
import PatientRegistration from './PatientRegistration';
import { getCurrentUser, signOut, AuthUser } from './auth';
import { invokeAgentStream } from './agentcore';
import './markdown.css';

interface Message {
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  feedback?: 'helpful' | 'not-helpful';
  feedbackSubmitting?: boolean;
}

interface MessageFeedback {
  [messageIndex: number]: {
    feedback?: 'helpful' | 'not-helpful';
    submitting?: boolean;
    showCopySuccess?: boolean;
  };
}

type NavigationItem = 'chat' | 'patient-registration';

function App() {
  const [activePage, setActivePage] = useState<NavigationItem>('chat');
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState<AuthUser | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [messageFeedback, setMessageFeedback] = useState<MessageFeedback>({});
  const [showSupportPrompts, setShowSupportPrompts] = useState(true);
  const [navigationOpen, setNavigationOpen] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      setUser(null);
    } finally {
      setCheckingAuth(false);
    }
  };

  const handleSignOut = () => {
    signOut();
    setUser(null);
    setMessages([]);
  };

  const handleAuthSuccess = async () => {
    setShowAuthModal(false);
    await checkAuth();
  };

  const handleFeedback = async (messageIndex: number, feedbackType: 'helpful' | 'not-helpful') => {
    // Set submitting state
    setMessageFeedback(prev => ({
      ...prev,
      [messageIndex]: { ...prev[messageIndex], submitting: true }
    }));

    // Simulate feedback submission (you can add actual API call here)
    await new Promise(resolve => setTimeout(resolve, 500));

    // Set feedback submitted
    setMessageFeedback(prev => ({
      ...prev,
      [messageIndex]: { feedback: feedbackType, submitting: false }
    }));
  };

  const handleCopy = async (messageIndex: number, content: string) => {
    try {
      await navigator.clipboard.writeText(content);

      // Show success indicator
      setMessageFeedback(prev => ({
        ...prev,
        [messageIndex]: { ...prev[messageIndex], showCopySuccess: true }
      }));

      // Hide success indicator after 2 seconds
      setTimeout(() => {
        setMessageFeedback(prev => ({
          ...prev,
          [messageIndex]: { ...prev[messageIndex], showCopySuccess: false }
        }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const cleanResponse = (response: string): string => {
    // Remove surrounding quotes if present
    let cleaned = response.trim();
    if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
      (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
      cleaned = cleaned.slice(1, -1);
    }

    // Replace literal \n with actual newlines
    cleaned = cleaned.replace(/\\n/g, '\n');

    // Replace literal \t with actual tabs
    cleaned = cleaned.replace(/\\t/g, '\t');

    return cleaned;
  };

  const handleSupportPromptClick = (promptText: string) => {
    // Fill the prompt input with the selected text
    setPrompt(promptText);
    // Hide support prompts after selection
    setShowSupportPrompts(false);
  };

  const handleSendMessage = async () => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }

    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    // Hide support prompts when sending a message
    setShowSupportPrompts(false);

    const userMessage: Message = {
      type: 'user',
      content: prompt,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError('');
    const currentPrompt = prompt;
    setPrompt('');

    // Create initial empty agent message for streaming
    const agentMessageIndex = messages.length + 1; // +1 because we just added user message
    const initialAgentMessage: Message = {
      type: 'agent',
      content: '',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, initialAgentMessage]);

    try {
      // Use streaming for real-time response
      await invokeAgentStream(
        { prompt: currentPrompt },
        // onChunk - called for each streaming chunk
        (chunk: string) => {
          setMessages(prev => {
            const newMessages = [...prev];
            const agentMsg = newMessages[agentMessageIndex];
            if (agentMsg && agentMsg.type === 'agent') {
              agentMsg.content += cleanResponse(chunk);
            }
            return newMessages;
          });
        },
        // onComplete - called when streaming is done
        (fullResponse: string) => {
          setMessages(prev => {
            const newMessages = [...prev];
            const agentMsg = newMessages[agentMessageIndex];
            if (agentMsg && agentMsg.type === 'agent') {
              agentMsg.content = cleanResponse(fullResponse);
            }
            return newMessages;
          });
          setLoading(false);
          // Show support prompts after agent responds
          setShowSupportPrompts(true);
        },
        // onError - called if streaming fails
        (error: Error) => {
          console.error('Streaming error:', error);
          setError(error.message);
          setLoading(false);
          // Remove the empty agent message on error
          setMessages(prev => prev.slice(0, -1));
        }
      );
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
      // Remove the empty agent message on error
      setMessages(prev => prev.slice(0, -1));
    }
  };

  // Get contextual support prompts based on conversation
  const getSupportPrompts = () => {
    // Initial prompts when no messages
    if (messages.length === 0) {
      return [
        { id: 'diabetes-basics', text: 'What is diabetes?' },
        { id: 'symptoms', text: 'What are the symptoms of diabetes?' },
        { id: 'diet', text: 'What foods should diabetics avoid?' },
        { id: 'treatment', text: 'How is diabetes treated?' }
      ];
    }

    // Contextual prompts based on last message
    const lastMessage = messages[messages.length - 1];
    if (lastMessage.type === 'agent') {
      const content = lastMessage.content.toLowerCase();

      // After diabetes information
      if (content.includes('diabetes') || content.includes('blood sugar') || content.includes('insulin')) {
        return [
          { id: 'complications', text: 'What are the complications of diabetes?' },
          { id: 'prevention', text: 'How can diabetes be prevented?' },
          { id: 'types', text: 'What are the different types of diabetes?' }
        ];
      }

      // After symptoms
      if (content.includes('symptoms') || content.includes('thirst') || content.includes('urination')) {
        return [
          { id: 'diagnosis', text: 'How is diabetes diagnosed?' },
          { id: 'treatment-follow', text: 'What are the treatment options?' },
          { id: 'diet-follow', text: 'What diet should I follow?' }
        ];
      }

      // After diet/food information
      if (content.includes('food') || content.includes('diet') || content.includes('avoid')) {
        return [
          { id: 'exercise', text: 'What exercises are good for diabetics?' },
          { id: 'monitoring', text: 'How often should I check blood sugar?' },
          { id: 'meal-planning', text: 'Help me plan diabetic-friendly meals' }
        ];
      }
    }

    // Default follow-up prompts
    return [
      { id: 'more', text: 'Tell me more' },
      { id: 'management', text: 'How do I manage diabetes?' },
      { id: 'lifestyle', text: 'What lifestyle changes should I make?' }
    ];
  };



  const renderContent = () => {
    if (activePage === 'patient-registration') {
      return (
        <ContentLayout defaultPadding>
          <PatientRegistration />
        </ContentLayout>
      );
    }

    // Default: Chat page
    return (
      <ContentLayout defaultPadding>
        <Grid
          gridDefinition={[
            { colspan: { default: 12, xs: 1, s: 2 } },
            { colspan: { default: 12, xs: 10, s: 8 } },
            { colspan: { default: 12, xs: 1, s: 2 } }
          ]}
        >
          <div />
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError('')}>
                {error}
              </Alert>
            )}

            <Container>
              <div role="region" aria-label="Chat">
                <SpaceBetween size="m">
                  {messages.length === 0 ? (
                    <Box textAlign="center" padding={{ vertical: 'xxl' }} color="text-body-secondary">
                      Welcome to Medview Connect! Ask me about diabetes, symptoms, treatments, diet, and healthcare information.
                    </Box>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {messages.map((message, index) => {
                        const feedback = messageFeedback[index];
                        const isAgent = message.type === 'agent';

                        return (
                          <div key={index} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                            {isAgent && (
                              <Avatar
                                ariaLabel="Generative AI assistant"
                                tooltipText="Generative AI assistant"
                                iconName="gen-ai"
                                color="gen-ai"
                              />
                            )}
                            <div style={{ flex: 1 }}>
                              <ChatBubble
                                type={message.type === 'user' ? 'outgoing' : 'incoming'}
                                ariaLabel={`${message.type === 'user' ? 'User' : 'Generative AI assistant'} message`}
                                avatar={message.type === 'user' ? <div /> : undefined}
                              >
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  components={{
                                    // Style code blocks
                                    code: ({ className, children }: any) => {
                                      const inline = !className;
                                      return inline ? (
                                        <code style={{
                                          backgroundColor: '#f4f4f4',
                                          padding: '2px 6px',
                                          borderRadius: '3px',
                                          fontFamily: 'monospace',
                                          fontSize: '0.9em'
                                        }}>
                                          {children}
                                        </code>
                                      ) : (
                                        <pre style={{
                                          backgroundColor: '#f4f4f4',
                                          padding: '12px',
                                          borderRadius: '6px',
                                          overflow: 'auto',
                                          fontFamily: 'monospace',
                                          fontSize: '0.9em'
                                        }}>
                                          <code className={className}>
                                            {children}
                                          </code>
                                        </pre>
                                      );
                                    },
                                    // Style links
                                    a: ({ children, href }: any) => (
                                      <a href={href} style={{ color: '#0972d3' }} target="_blank" rel="noopener noreferrer">
                                        {children}
                                      </a>
                                    ),
                                    // Style lists
                                    ul: ({ children }: any) => (
                                      <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '8px' }}>
                                        {children}
                                      </ul>
                                    ),
                                    ol: ({ children }: any) => (
                                      <ol style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '8px' }}>
                                        {children}
                                      </ol>
                                    ),
                                    // Style paragraphs
                                    p: ({ children }: any) => (
                                      <p style={{ marginTop: '8px', marginBottom: '8px' }}>
                                        {children}
                                      </p>
                                    ),
                                  }}
                                >
                                  {message.content}
                                </ReactMarkdown>
                              </ChatBubble>

                              {isAgent && (
                                <div style={{ marginTop: '8px' }}>
                                  <ButtonGroup
                                    variant="icon"
                                    ariaLabel="Message actions"
                                    items={[
                                      {
                                        type: 'icon-button',
                                        id: 'thumbs-up',
                                        iconName: feedback?.feedback === 'helpful' ? 'thumbs-up-filled' : 'thumbs-up',
                                        text: 'Helpful',
                                        disabled: feedback?.submitting || !!feedback?.feedback,
                                        loading: feedback?.submitting && feedback?.feedback !== 'not-helpful',
                                        disabledReason: feedback?.feedback === 'helpful'
                                          ? '"Helpful" feedback has been submitted.'
                                          : feedback?.feedback === 'not-helpful'
                                            ? '"Helpful" option is unavailable after "not helpful" feedback submitted.'
                                            : undefined,
                                      },
                                      {
                                        type: 'icon-button',
                                        id: 'thumbs-down',
                                        iconName: feedback?.feedback === 'not-helpful' ? 'thumbs-down-filled' : 'thumbs-down',
                                        text: 'Not helpful',
                                        disabled: feedback?.submitting || !!feedback?.feedback,
                                        loading: feedback?.submitting && feedback?.feedback !== 'helpful',
                                        disabledReason: feedback?.feedback === 'not-helpful'
                                          ? '"Not helpful" feedback has been submitted.'
                                          : feedback?.feedback === 'helpful'
                                            ? '"Not helpful" option is unavailable after "helpful" feedback submitted.'
                                            : undefined,
                                      },
                                      {
                                        type: 'icon-button',
                                        id: 'copy',
                                        iconName: 'copy',
                                        text: 'Copy',
                                        popoverFeedback: feedback?.showCopySuccess ? (
                                          <StatusIndicator type="success">
                                            Copied
                                          </StatusIndicator>
                                        ) : undefined,
                                      }
                                    ]}
                                    onItemClick={({ detail }) => {
                                      if (detail.id === 'thumbs-up') {
                                        handleFeedback(index, 'helpful');
                                      } else if (detail.id === 'thumbs-down') {
                                        handleFeedback(index, 'not-helpful');
                                      } else if (detail.id === 'copy') {
                                        handleCopy(index, message.content);
                                      }
                                    }}
                                  />
                                  {feedback?.feedback && (
                                    <Box margin={{ top: 'xs' }} color="text-status-info" fontSize="body-s">
                                      Feedback submitted
                                    </Box>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      {loading && (
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                          <Avatar
                            ariaLabel="Generative AI assistant"
                            tooltipText="Generative AI assistant"
                            iconName="gen-ai"
                            color="gen-ai"
                            loading={true}
                          />
                          <Box color="text-body-secondary">
                            Generating a response
                          </Box>
                        </div>
                      )}
                    </div>
                  )}

                  {showSupportPrompts && !loading && (
                    <SupportPromptGroup
                      onItemClick={({ detail }) => handleSupportPromptClick(
                        getSupportPrompts().find(p => p.id === detail.id)?.text || ''
                      )}
                      ariaLabel="Suggested prompts"
                      alignment="horizontal"
                      items={getSupportPrompts()}
                    />
                  )}

                  <PromptInput
                    value={prompt}
                    onChange={({ detail }) => setPrompt(detail.value)}
                    onAction={handleSendMessage}
                    placeholder="Ask about diabetes, symptoms, treatments, or diet..."
                    actionButtonAriaLabel="Send message"
                    actionButtonIconName="send"
                    disabled={loading}
                  />
                </SpaceBetween>
              </div>
            </Container>
          </SpaceBetween>
          <div />
        </Grid>
      </ContentLayout>
    );
  };

  if (checkingAuth) {
    return (
      <>
        <TopNavigation
          identity={{
            href: "#",
            title: "Medview Connect",
            logo: {
              src: "/medview-logo.svg",
              alt: "Medview Connect"
            }
          }}
          utilities={[
            {
              type: "button",
              text: user ? `${user.email} | Sign Out` : "Sign In",
              iconName: user ? "user-profile" : "lock-private",
              onClick: () => {
                if (user) {
                  handleSignOut();
                } else {
                  setShowAuthModal(true);
                }
              }
            }
          ]}
          i18nStrings={{
            overflowMenuTriggerText: "More",
            overflowMenuTitleText: "All"
          }}
        />
        <AppLayout
          navigationHide={true}
          toolsHide={true}
          disableContentPaddings
          contentType="default"
          content={
            <ContentLayout defaultPadding>
              <Box textAlign="center" padding="xxl">
                Loading...
              </Box>
            </ContentLayout>
          }
        />
      </>
    );
  }

  return (
    <>
      <AuthModal
        visible={showAuthModal}
        onDismiss={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
      />
      <TopNavigation
        identity={{
          href: "#",
          title: "Medview Connect",
          logo: {
            src: "/medview-logo.svg",
            alt: "Medview Connect"
          }
        }}
        utilities={[
          {
            type: "button",
            text: user ? `${user.email} | Sign Out` : "Sign In",
            iconName: user ? "user-profile" : "lock-private",
            onClick: () => {
              if (user) {
                handleSignOut();
              } else {
                setShowAuthModal(true);
              }
            }
          }
        ]}
        i18nStrings={{
          overflowMenuTriggerText: "More",
          overflowMenuTitleText: "All"
        }}
      />
      <AppLayout
        navigation={
          <SideNavigation
            activeHref={`#${activePage}`}
            header={{
              href: "#",
              text: "Medview Connect"
            }}
            onFollow={(event) => {
              event.preventDefault();
              const page = event.detail.href.substring(1) as NavigationItem;
              setActivePage(page);
            }}
            items={[
              {
                type: "link",
                text: "AI Assistant",
                href: "#chat"
              },
              {
                type: "divider"
              },
              {
                type: "section",
                text: "Patient Management",
                items: [
                  {
                    type: "link",
                    text: "Register Patient",
                    href: "#patient-registration"
                  }
                ]
              }
            ]}
          />
        }
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        toolsHide={true}
        disableContentPaddings
        contentType="default"
        content={renderContent()}
      />
    </>
  );
}

export default App;
