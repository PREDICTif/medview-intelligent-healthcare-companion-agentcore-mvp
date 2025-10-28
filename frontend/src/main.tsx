import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import AppStreaming from './AppStreaming';
import '@cloudscape-design/global-styles/index.css';

// Use streaming app if WebSocket URL is configured
const useStreaming = !!import.meta.env.VITE_WEBSOCKET_URL;
const AppComponent = useStreaming ? AppStreaming : App;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppComponent />
  </React.StrictMode>
);
