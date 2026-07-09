import React, { useState } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { DocumentUpload } from './components/DocumentUpload';
import { useChat } from './hooks/useChat';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const {
    messages,
    sendMessage,
    isLoading,
    error,
    clearError,
    documents,
    uploadDocument,
    isUploading,
    uploadStatus,
    clearUploadStatus
  } = useChat();

  return (
    <div className="app-container">
      {/* Mobile Sidebar Toggle & Overlay */}
      <button 
        className="sidebar-toggle" 
        onClick={() => setSidebarOpen(true)}
        aria-label="Open sidebar"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>

      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar - Document Management */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Knowledge Base</h2>
          <p>Manage your documents for RAG</p>
        </div>
        
        <DocumentUpload 
          onUpload={uploadDocument}
          documents={documents}
          isUploading={isUploading}
          uploadStatus={uploadStatus}
          clearStatus={clearUploadStatus}
        />
      </aside>

      {/* Main Chat Area */}
      <ChatInterface 
        messages={messages}
        onSendMessage={sendMessage}
        isLoading={isLoading}
        error={error}
        clearError={clearError}
        hasDocuments={documents.length > 0}
      />
    </div>
  );
}
