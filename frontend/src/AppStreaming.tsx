import { useState, useEffect } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import ContentLayout from '@cloudscape-design/components/content-layout';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Alert from '@cloudscape-design/components/alert';
import AuthModal from './AuthModal';
import StreamingChat from './components/StreamingChat';
import { getCurrentUser, signOut, AuthUser } from './auth';

function AppStreaming() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const webSocketUrl = import.meta.env.VITE_WEBSOCKET_URL || null;
  const agentRuntimeArn = import.meta.env.VITE_AGENT_RUNTIME_ARN || '';
  const region = import.meta.env.VITE_REGION || 'us-east-1';

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
  };

  const handleAuthSuccess = async () => {
    setShowAuthModal(false);
    await checkAuth();
  };

  return (
    <>
      <TopNavigation
        identity={{
          href: '/',
          title: 'Amazon Bedrock AgentCore Demo',
        }}
        utilities={[
          {
            type: 'button',
            text: user ? user.email : 'Sign In',
            onClick: () => {
              if (user) {
                handleSignOut();
              } else {
                setShowAuthModal(true);
              }
            },
          },
        ]}
      />

      <AppLayout
        toolsHide={true}
        navigationHide={true}
        content={
          <ContentLayout
            header={
              <SpaceBetween size="m">
                <div>
                  <h1>Streaming Chat (WebSocket)</h1>
                  <p>Real-time streaming responses powered by Amazon Bedrock</p>
                </div>
              </SpaceBetween>
            }
          >
            <SpaceBetween size="l">
              {!user && !checkingAuth && (
                <Alert type="info">
                  Please sign in to start chatting with streaming responses.
                </Alert>
              )}

              {user && webSocketUrl && (
                <StreamingChat
                  webSocketUrl={webSocketUrl}
                  agentRuntimeArn={agentRuntimeArn}
                  region={region}
                />
              )}

              {user && !webSocketUrl && (
                <Alert type="warning">
                  WebSocket URL not configured. Streaming is not available.
                </Alert>
              )}
            </SpaceBetween>
          </ContentLayout>
        }
      />

      <AuthModal
        visible={showAuthModal}
        onDismiss={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
      />
    </>
  );
}

export default AppStreaming;

