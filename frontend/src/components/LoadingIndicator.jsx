import React from 'react';

export function LoadingIndicator() {
  return (
    <div className="loading-indicator">
      <div className="loading-dots">
        <div className="loading-dot"></div>
        <div className="loading-dot"></div>
        <div className="loading-dot"></div>
      </div>
      <span className="loading-text">Thinking...</span>
    </div>
  );
}
