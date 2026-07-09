import React, { useCallback, useState } from 'react';

export function DocumentUpload({ 
  onUpload, 
  documents, 
  isUploading, 
  uploadStatus, 
  clearStatus 
}) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUpload(e.dataTransfer.files[0]);
    }
  }, [onUpload]);

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndUpload(e.target.files[0]);
    }
    // Reset input so same file can be selected again if needed
    e.target.value = null;
  };

  const validateAndUpload = (file) => {
    // Client-side validation
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (ext !== '.pdf' && ext !== '.txt') {
      alert('Only .pdf and .txt files are supported.');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB.');
      return;
    }

    onUpload(file);
  };

  return (
    <div className="sidebar-content">
      {/* Upload Area */}
      <div 
        className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && document.getElementById('file-upload').click()}
      >
        <input 
          type="file" 
          id="file-upload" 
          accept=".pdf,.txt" 
          style={{ display: 'none' }} 
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        
        <span className="upload-icon">📄</span>
        <p>
          <span className="upload-cta">Click to upload</span> or drag and drop
        </p>
        <p className="upload-hint">PDF or TXT (Max 10MB)</p>
        
        {isUploading && (
          <div className="upload-progress">
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: '100%' }}></div>
            </div>
            <div className="upload-status">Processing document...</div>
          </div>
        )}
      </div>

      {/* Status Banner */}
      {uploadStatus && !isUploading && (
        <div className={`error-banner`} style={{
          backgroundColor: uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          borderColor: uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
          color: uploadStatus.type === 'success' ? '#6ee7b7' : '#fca5a5'
        }}>
          <span style={{flex: 1}}>{uploadStatus.message}</span>
          <button className="error-banner-dismiss" onClick={clearStatus}>&times;</button>
        </div>
      )}

      {/* Document List */}
      {documents.length > 0 && (
        <div className="document-list-container" style={{ marginTop: '32px' }}>
          <h3 className="document-list-title">Knowledge Base</h3>
          <ul className="document-list">
            {documents.map((doc, idx) => (
              <li key={idx} className="document-item">
                <span className="document-item-icon">
                  {doc.file_type === 'pdf' ? '📕' : '📝'}
                </span>
                <div className="document-item-info">
                  <div className="document-item-name" title={doc.filename}>
                    {doc.filename}
                  </div>
                  <div className="document-item-meta">
                    {doc.num_chunks} segments indexed
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
