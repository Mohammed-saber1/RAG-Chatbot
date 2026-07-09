import React, { useState } from 'react';

export function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);

  // Extract the original filename without the UUID prefix if it exists
  // Assuming the format might be UUID.ext or just filename.ext
  // The backend now returns original filename via metadata, so we can use it directly
  const displayName = source.filename;

  return (
    <div className={`source-card ${expanded ? 'expanded' : ''}`} onClick={() => setExpanded(!expanded)}>
      <div className="source-card-header">
        <div className="source-card-filename">
          <span>📄</span>
          {displayName}
        </div>
        {source.page && (
          <div className="source-card-page">Page {source.page}</div>
        )}
      </div>
      
      <div className="source-card-preview">
        "{source.chunk_preview.trim()}..."
      </div>
      
      <div className="source-card-toggle">
        {expanded ? 'Show less' : 'Read more'}
      </div>
    </div>
  );
}
