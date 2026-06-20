'use client';

import { useState, useEffect } from 'react';
import UploadModal from './UploadModal';

export default function Sidebar({ isOpen, toggleSidebar }) {
  const [stats, setStats] = useState({ total_chunks: 0, document_count: 0, documents: [] });
  const [loading, setLoading] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleUploadSuccess = () => {
    fetchStats();
  };

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'visible' : ''}`} onClick={toggleSidebar}></div>
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">⚖️</div>
          <div>
            <h1 className="sidebar-title">Nyaya AI</h1>
            <p className="sidebar-subtitle">Indian Law Assistant</p>
          </div>
        </div>

        <div className="sidebar-content">
          <div className="sidebar-section">
            <h2 className="sidebar-section-title">Knowledge Base Stats</h2>
            {loading ? (
              <div className="stats-grid">
                <div className="stat-card shimmer" style={{ height: '70px' }}></div>
                <div className="stat-card shimmer" style={{ height: '70px' }}></div>
              </div>
            ) : (
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{stats.document_count}</div>
                  <div className="stat-label">Documents</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats.total_chunks.toLocaleString()}</div>
                  <div className="stat-label">Chunks</div>
                </div>
              </div>
            )}
          </div>

          <div className="sidebar-section">
            <h2 className="sidebar-section-title">Ingested Documents</h2>
            <div className="doc-list">
              {loading ? (
                <>
                  <div className="doc-item shimmer" style={{ height: '40px' }}></div>
                  <div className="doc-item shimmer" style={{ height: '40px' }}></div>
                  <div className="doc-item shimmer" style={{ height: '40px' }}></div>
                </>
              ) : stats.documents.length === 0 ? (
                <div className="doc-item">
                  <span className="doc-icon">📄</span>
                  <span className="doc-name">No documents yet</span>
                </div>
              ) : (
                stats.documents.map((doc, idx) => (
                  <div key={idx} className="doc-item" title={doc}>
                    <span className="doc-icon">📄</span>
                    <span className="doc-name">{doc}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="sidebar-section" style={{ marginTop: 'auto', marginBottom: 0 }}>
            <div className="upload-zone" onClick={() => setIsUploadOpen(true)}>
              <div className="upload-icon">📤</div>
              <div className="upload-text">
                <strong>Upload new PDF</strong><br/>
                Add to knowledge base
              </div>
            </div>
          </div>
        </div>
      </aside>

      {isUploadOpen && (
        <UploadModal 
          onClose={() => setIsUploadOpen(false)} 
          onSuccess={handleUploadSuccess} 
        />
      )}
    </>
  );
}
