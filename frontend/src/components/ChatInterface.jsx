import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { LoadingIndicator } from './LoadingIndicator';

export function ChatInterface({ 
  messages, 
  onSendMessage, 
  isLoading, 
  error, 
  clearError,
  hasDocuments
}) {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="chat-main">
      <div className="chat-header">
        <div className="chat-header-title">
          <div className="chat-header-logo">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
              <path d="M12 12 2.1 7.1"></path>
              <path d="M12 12l9.9 4.9"></path>
            </svg>
          </div>
          <h1>DocQuery AI</h1>
        </div>
        <div className="chat-header-status">
          <div className="status-dot"></div>
          Online
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span style={{flex: 1}}>{error}</span>
          <button className="error-banner-dismiss" onClick={clearError}>&times;</button>
        </div>
      )}

      {messages.length === 0 ? (
        <div className="welcome-container">
          <span className="welcome-icon">🧠</span>
          <h2>Chat with your Documents</h2>
          <p>
            Upload PDFs or text files to the knowledge base, then ask questions. 
            The AI will answer exclusively based on the provided context.
          </p>
          
          <div className="welcome-steps">
            <div className="welcome-step">
              <span className="welcome-step-icon">📤</span>
              <div className="welcome-step-title">Upload</div>
              <div className="welcome-step-desc">Add PDF or TXT files to your knowledge base</div>
            </div>
            <div className="welcome-step">
              <span className="welcome-step-icon">🔍</span>
              <div className="welcome-step-title">Analyze</div>
              <div className="welcome-step-desc">Documents are split and locally embedded</div>
            </div>
            <div className="welcome-step">
              <span className="welcome-step-icon">💬</span>
              <div className="welcome-step-title">Query</div>
              <div className="welcome-step-desc">Ask questions and get answers with exact source citations</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && !messages.some(m => m.isStreaming) && (
             <LoadingIndicator />
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      <ChatInput 
        onSend={onSendMessage} 
        disabled={isLoading || !hasDocuments} 
      />
    </div>
  );
}
