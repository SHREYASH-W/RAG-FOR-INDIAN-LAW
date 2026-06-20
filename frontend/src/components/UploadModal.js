'use client';

import { useState, useRef } from 'react';

export default function UploadModal({ onClose, onSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState({ type: '', message: '' });
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (f) => {
    if (!f) return;
    if (f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) {
      setStatus({ type: 'error', message: 'Please upload a PDF file.' });
      return;
    }
    setFile(f);
    setStatus({ type: '', message: '' });
    handleUpload(f);
  };

  const handleUpload = async (fileToUpload) => {
    if (!fileToUpload) return;
    
    setIsUploading(true);
    setProgress(10); // Start progress
    setStatus({ type: 'loading', message: 'Uploading and indexing...' });

    // Simulate progress while uploading
    const progressInterval = setInterval(() => {
      setProgress(p => Math.min(p + 5, 85));
    }, 500);

    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      const data = await res.json();
      
      if (res.ok) {
        if (data.status === 'skipped') {
            setStatus({ type: 'success', message: `Skipped: ${fileToUpload.name} is already indexed.` });
        } else {
            setStatus({ type: 'success', message: `Success! Added ${data.chunks_added} chunks.` });
        }
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      } else {
        setStatus({ type: 'error', message: data.detail || 'Upload failed.' });
        setIsUploading(false);
      }
    } catch (error) {
      clearInterval(progressInterval);
      setStatus({ type: 'error', message: 'Network error. Backend might be down.' });
      setIsUploading(false);
    }
  };

  return (
    <div style={modalOverlayStyle}>
      <div style={modalContentStyle}>
        <div style={headerStyle}>
          <h2 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--text-primary)' }}>Add to Knowledge Base</h2>
          <button onClick={onClose} style={closeBtnStyle}>✕</button>
        </div>

        <div 
          className={`upload-zone ${isDragging ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          style={{ minHeight: '180px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept=".pdf" 
            className="upload-input" 
          />
          
          <div className="upload-icon">📄</div>
          {!file ? (
            <div className="upload-text">
              <strong>Click to upload</strong> or drag and drop<br/>
              PDF files only
            </div>
          ) : (
            <div className="upload-text">
              <strong>{file.name}</strong><br/>
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </div>
          )}

          {isUploading && (
            <div className="upload-progress" style={{ width: '80%', margin: '16px auto 0' }}>
              <div className="upload-progress-bar">
                <div className="upload-progress-fill" style={{ width: `${progress}%` }}></div>
              </div>
            </div>
          )}
        </div>

        {status.message && (
          <div className={status.type === 'error' ? 'upload-error' : status.type === 'success' ? 'upload-success' : 'upload-status'} style={{ textAlign: 'center', marginTop: '16px' }}>
            {status.type === 'success' && <span style={{fontSize: '1.2rem'}}>✅</span>}
            {status.message}
          </div>
        )}
      </div>
    </div>
  );
}

const modalOverlayStyle = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  backdropFilter: 'blur(4px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalContentStyle = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-accent)',
  borderRadius: 'var(--radius-xl)',
  width: '90%',
  maxWidth: '500px',
  padding: '24px',
  boxShadow: 'var(--shadow-lg), 0 0 40px rgba(212, 168, 83, 0.1)',
  animation: 'fadeIn 0.3s ease',
};

const headerStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '20px',
};

const closeBtnStyle = {
  fontSize: '1.2rem',
  color: 'var(--text-tertiary)',
  padding: '4px',
};
