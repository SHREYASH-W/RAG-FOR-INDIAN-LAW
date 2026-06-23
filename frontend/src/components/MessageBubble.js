'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function MessageBubble({ message, onCopy }) {
  const isUser = message.role === 'user';
  const isTyping = message.content === 'typing';
  const [feedback, setFeedback] = useState(null); // 'up' | 'down' | null

  const confidenceLevel = 
    message.confidence >= 0.7 ? 'high' :
    message.confidence >= 0.4 ? 'medium' : 'low';

  const handleFeedback = (type) => {
    setFeedback(prev => prev === type ? null : type);
  };

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-ai'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '⚖️'}
      </div>

      <div className="message-body">
        <div className="message-role">
          {isUser ? 'You' : 'Nyaya AI'}
        </div>

        <div className="message-content">
          {isTyping ? (
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

        {/* Action bar — only on AI responses, not on typing */}
        {!isUser && !isTyping && (
          <div className="message-actions">
            {/* Confidence indicator */}
            {message.confidence > 0 && (
              <span className="action-btn" style={{ cursor: 'default' }}>
                <span className={`confidence-dot confidence-${confidenceLevel}`}></span>
                {confidenceLevel === 'high' ? 'High confidence' :
                 confidenceLevel === 'medium' ? 'Moderate confidence' : 'Low confidence'}
              </span>
            )}

            {/* Copy button */}
            <button
              className="action-btn"
              onClick={() => onCopy?.(message.content)}
              title="Copy response"
            >
              <span className="action-btn-icon">📋</span>
              Copy
            </button>

            {/* Feedback buttons */}
            <button
              className={`action-btn ${feedback === 'up' ? 'active' : ''}`}
              onClick={() => handleFeedback('up')}
              title="Good response"
            >
              <span className="action-btn-icon">👍</span>
            </button>
            <button
              className={`action-btn ${feedback === 'down' ? 'active' : ''}`}
              onClick={() => handleFeedback('down')}
              title="Poor response"
            >
              <span className="action-btn-icon">👎</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
