import { useState, useRef, useEffect } from 'react';

/**
 * Custom hook for managing the chat state, streaming responses, and document uploads.
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const abortControllerRef = useRef(null);

  // Fetch initial documents list
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch('/api/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const uploadDocument = async (file) => {
    setIsUploading(true);
    setUploadStatus({ type: 'info', message: 'Uploading and processing...' });
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setUploadStatus({
        type: 'success',
        message: `Successfully indexed ${data.num_chunks} chunks from ${data.filename}`,
      });
      fetchDocuments(); // Refresh the list
    } catch (err) {
      console.error('Upload error:', err);
      setUploadStatus({
        type: 'error',
        message: err.message || 'Failed to upload document',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const sendMessage = async (question) => {
    if (!question.trim() || isLoading) return;

    // Cancel any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    // Add user message immediately
    const userMessage = { id: Date.now(), role: 'user', content: question };
    setMessages((prev) => [...prev, userMessage]);
    
    // Add an empty assistant message that will be updated via streaming
    const aiMessageId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      { id: aiMessageId, role: 'assistant', content: '', sources: null, isStreaming: true },
    ]);
    
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to get a response');
      }

      // Handle SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let aiContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (!dataStr.trim()) continue;

            try {
              const event = JSON.parse(dataStr);

              if (event.type === 'token') {
                aiContent += event.content;
                // Update the message content incrementally
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, content: aiContent }
                      : msg
                  )
                );
              } else if (event.type === 'sources') {
                // Attach sources to the message
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, sources: event.sources }
                      : msg
                  )
                );
              } else if (event.type === 'error') {
                throw new Error(event.content);
              } else if (event.type === 'done') {
                // Stream finished
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, isStreaming: false }
                      : msg
                  )
                );
              }
            } catch (e) {
              console.warn('Failed to parse SSE event:', e, 'Raw data:', dataStr);
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Chat error:', err);
        setError(err.message || 'An error occurred during chat.');
        // Mark as no longer streaming on error
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, isStreaming: false }
              : msg
          )
        );
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      // Mark last message as not streaming
      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const newMessages = [...prev];
        const lastIndex = newMessages.length - 1;
        if (newMessages[lastIndex].role === 'assistant' && newMessages[lastIndex].isStreaming) {
           newMessages[lastIndex].isStreaming = false;
        }
        return newMessages;
      });
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
    if (abortControllerRef.current) {
       abortControllerRef.current.abort();
    }
  };

  return {
    messages,
    sendMessage,
    isLoading,
    error,
    clearError: () => setError(null),
    stopGeneration,
    clearChat,
    documents,
    uploadDocument,
    isUploading,
    uploadStatus,
    clearUploadStatus: () => setUploadStatus(null)
  };
}
