import React from 'react';
import { SourceCard } from './SourceCard';

export function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="message-content">
          {/* Use textContent behavior via React children to prevent XSS. 
              No dangerouslySetInnerHTML used. */}
          <div className="message-text">
            {message.content}
            {message.isStreaming && <span className="typing-cursor">▌</span>}
          </div>
        </div>

        {/* Render sources if available and it's an assistant message */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="sources-container">
            <div className="sources-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '4px' }}>
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
              </svg>
              Sources
            </div>
            {message.sources.map((source, idx) => (
              <SourceCard key={`${source.filename}-${source.page}-${idx}`} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
      </div >
    </div >
  );
}
