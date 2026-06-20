'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-ai'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '⚖️'}
      </div>
      
      <div className="message-body">
        <div className="message-content">
          {message.content === 'typing' ? (
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          ) : isUser ? (
            message.content
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>
        
        {!isUser && message.content !== 'typing' && message.sources && message.sources.length > 0 && (
          <div className="sources-container">
            <button 
              className="sources-toggle"
              onClick={() => setSourcesOpen(!sourcesOpen)}
            >
              <span className={`sources-toggle-icon ${sourcesOpen ? 'open' : ''}`}>▼</span>
              {message.sources.length} Legal Sources
            </button>
            
            {sourcesOpen && (
              <div className="sources-list">
                {message.sources.map((source, idx) => (
                  <div key={idx} className="source-card">
                    <div className="source-header">
                      <div className="source-act">{source.act_name}</div>
                      <div className="source-score" title="Relevance Score">
                        {Math.round(source.score * 100)}% Match
                      </div>
                    </div>
                    
                    <div className="source-meta">
                      {source.part && <div className="source-meta-item"><span>Part:</span> {source.part.replace('Part ', '')}</div>}
                      {source.chapter && <div className="source-meta-item"><span>Chapter:</span> {source.chapter.replace('Chapter ', '')}</div>}
                      {source.article && <div className="source-meta-item"><span>Article:</span> {source.article}</div>}
                      {source.section && <div className="source-meta-item"><span>Section:</span> {source.section}</div>}
                      {source.page && <div className="source-meta-item"><span>Page:</span> {source.page}</div>}
                    </div>
                    
                    <div className="source-excerpt">
                      "{source.excerpt}"
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
