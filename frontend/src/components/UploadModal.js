'use client';

import { useState, useRef } from 'react';

export default function UploadModal({ onClose }) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState({ type: '', message: '' });
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = Array.from(e.dataTransfer.files);
    addFiles(dropped);
  };

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files);
    addFiles(selected);
    e.target.value = '';
  };

  const addFiles = (newFiles) => {
    const valid = newFiles.filter(f => {
      const name = f.name.toLowerCase();
      return name.endsWith('.pdf') || name.endsWith('.json');
    });

    if (valid.length === 0) {
      setStatus({ type: 'error', message: 'Only PDF and JSON files are supported.' });
      return;
    }

    setFiles(prev => {
      // Deduplicate by name
      const existingNames = new Set(prev.map(f => f.name));
      const unique = valid.filter(f => !existingNames.has(f.name));
      return [...prev, ...unique];
    });
    setStatus({ type: '', message: '' });
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    setProgress(5);
    setStatus({
      type: 'loading',
      message: `Uploading and indexing ${files.length} file${files.length > 1 ? 's' : ''}…`,
    });

    const progressInterval = setInterval(() => {
      setProgress(p => Math.min(p + 3, 88));
    }, 600);

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      const data = await res.json();

      if (res.ok) {
        setStatus({
          type: 'success',
          message: data.message || 'Documents added to knowledge base successfully.',
        });
        setTimeout(() => onClose(), 2500);
      } else {
        setStatus({
          type: 'error',
          message: data.detail || 'Upload failed. Please try again.',
        });
        setIsUploading(false);
      }
    } catch {
      clearInterval(progressInterval);
      setStatus({
        type: 'error',
        message: 'Could not connect to the server. Ensure the backend is running.',
      });
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-overlay" onClick={(e) => {
      if (e.target === e.currentTarget && !isUploading) onClose();
    }}>
      <div className="upload-modal">
        {/* Header */}
        <div className="upload-modal-header">
          <div className="upload-modal-title">
            <span className="upload-modal-icon">📄</span>
            Add Documents
          </div>
          {!isUploading && (
            <button className="upload-close-btn" onClick={onClose}>✕</button>
          )}
        </div>

        <p className="upload-modal-desc">
          Upload PDF or JSON files to expand the legal knowledge base. 
          Multiple files can be added at once.
        </p>

        {/* Drop zone */}
        <div
          className={`upload-dropzone ${isDragging ? 'dragging' : ''} ${isUploading ? 'disabled' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.json"
            multiple
            hidden
          />
          <div className="dropzone-icon">{isDragging ? '📥' : '📤'}</div>
          <div className="dropzone-text">
            <strong>Click to browse</strong> or drag files here
          </div>
          <div className="dropzone-hint">PDF, JSON — up to 50 MB each</div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="upload-file-list">
            {files.map((file, i) => (
              <div key={`${file.name}-${i}`} className="upload-file-item">
                <div className="upload-file-info">
                  <span className="upload-file-ext">
                    {file.name.toLowerCase().endsWith('.pdf') ? '📕' : '📘'}
                  </span>
                  <span className="upload-file-name">{file.name}</span>
                  <span className="upload-file-size">{formatSize(file.size)}</span>
                </div>
                {!isUploading && (
                  <button
                    className="upload-file-remove"
                    onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Progress bar */}
        {isUploading && (
          <div className="upload-progress-wrap">
            <div className="upload-progress-track">
              <div
                className="upload-progress-bar"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="upload-progress-pct">{progress}%</span>
          </div>
        )}

        {/* Status */}
        {status.message && (
          <div className={`upload-status upload-status-${status.type}`}>
            {status.type === 'success' && <span>✅</span>}
            {status.type === 'error' && <span>⚠️</span>}
            {status.type === 'loading' && <span className="upload-spinner">⏳</span>}
            {status.message}
          </div>
        )}

        {/* Actions */}
        {!isUploading && !status.type?.includes('success') && (
          <div className="upload-actions">
            <button className="upload-cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button
              className="upload-submit-btn"
              onClick={handleUpload}
              disabled={files.length === 0}
            >
              Upload {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''}` : ''}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
