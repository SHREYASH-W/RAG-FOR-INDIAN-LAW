'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import MessageBubble from './MessageBubble';
import UploadModal from './UploadModal';

const API_BASE = '';

const SAMPLE_QUESTIONS = [
  {
    icon: '📜',
    text: 'What are the fundamental rights guaranteed under the Indian Constitution?',
  },
  {
    icon: '⚖️',
    text: 'Explain the procedure for arrest under the Bharatiya Nagarik Suraksha Sanhita.',
  },
  {
    icon: '💻',
    text: 'What is the penalty for cyber terrorism under the IT Act?',
  },
  {
    icon: '🛡️',
    text: 'Can a person be compelled to be a witness against themselves?',
  },
];

const CATEGORIES = [
  'Constitution', 'Criminal Law', 'IT Act', 'Civil Law', 'Fundamental Rights',
];

export default function ChatInterface() {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showCopied, setShowCopied] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Initialize with a fresh conversation
  useEffect(() => {
    startNewChat();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages]);

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  const startNewChat = useCallback(() => {
    const newConv = {
      id: Date.now().toString(),
      title: 'New conversation',
      messages: [],
      createdAt: new Date().toISOString(),
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversation(newConv);
    setInput('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  }, []);

  const handleSend = async (question) => {
    const textToSend = (question || input).trim();
    if (!textToSend || isLoading) return;

    // User message
    const userMsg = { role: 'user', content: textToSend };
    
    setActiveConversation(prev => {
      const updated = {
        ...prev,
        messages: [...prev.messages, userMsg],
        title: prev.messages.length === 0 
          ? textToSend.substring(0, 60) + (textToSend.length > 60 ? '…' : '')
          : prev.title,
      };
      setConversations(convs => convs.map(c => c.id === prev.id ? updated : c));
      return updated;
    });

    setInput('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
    setIsLoading(true);

    // Add typing indicator
    const typingMsg = { role: 'ai', content: 'typing' };
    setActiveConversation(prev => {
      const updated = { ...prev, messages: [...prev.messages, typingMsg] };
      return updated;
    });

    try {
      // Build chat history from current conversation (excluding typing)
      const chatHistory = activeConversation.messages
        .filter(m => m.content !== 'typing')
        .map(m => ({ role: m.role === 'ai' ? 'assistant' : m.role, content: m.content }));

      const res = await fetch(`${API_BASE}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: textToSend,
          chat_history: chatHistory,
        }),
      });

      const data = await res.json();

      // Replace typing indicator with actual response
      setActiveConversation(prev => {
        const msgs = [...prev.messages];
        msgs[msgs.length - 1] = {
          role: 'ai',
          content: data.answer || "I couldn't generate an answer. Please try again.",
          confidence: data.confidence || 0,
        };
        const updated = { ...prev, messages: msgs };
        setConversations(convs => convs.map(c => c.id === prev.id ? updated : c));
        return updated;
      });
    } catch (error) {
      console.error('Failed to get answer:', error);
      setActiveConversation(prev => {
        const msgs = [...prev.messages];
        msgs[msgs.length - 1] = {
          role: 'ai',
          content: 'Unable to connect to the server. Please ensure the backend is running on port 8000.',
          confidence: 0,
        };
        const updated = { ...prev, messages: msgs };
        setConversations(convs => convs.map(c => c.id === prev.id ? updated : c));
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setShowCopied(true);
    setTimeout(() => setShowCopied(false), 2000);
  };

  const messages = activeConversation?.messages || [];

  return (
    <div className="main-content">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header-inner">
          <div className="chat-header-left">
            <div className="header-logo">⚖️</div>
            <div className="chat-header-title">Nyaya AI</div>
          </div>
          <div className="chat-header-right">
            <button className="new-chat-btn" onClick={() => setIsUploadModalOpen(true)} style={{ marginRight: '8px' }}>
              📥 <span>Upload</span>
            </button>
            <div className="header-badge">
              <span className="header-badge-dot"></span>
              AI Active
            </div>
            <button className="new-chat-btn" onClick={startNewChat}>
              ✦ <span>New Chat</span>
            </button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-emblem">⚖️</div>
            <h1 className="welcome-heading">Indian Law Assistant</h1>
            <p className="welcome-subheading">
              Ask any question about Indian law — Constitution, BNS, BNSS, IT Act, 
              and more. Get precise, authoritative answers instantly.
            </p>

            <div className="welcome-categories">
              {CATEGORIES.map((cat) => (
                <span key={cat} className="category-pill">{cat}</span>
              ))}
            </div>

            <div className="sample-questions">
              {SAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  className="sample-question"
                  onClick={() => handleSend(q.text)}
                >
                  <span className="sample-question-icon">{q.icon}</span>
                  {q.text}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages-inner">
            {messages.map((msg, idx) => (
              <MessageBubble
                key={idx}
                message={msg}
                onCopy={handleCopy}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="input-area">
        <div className="input-area-inner">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask about Indian law…"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={1}
            />
            <button
              className="send-button"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              aria-label="Send message"
            >
              ↗
            </button>
          </div>
          <div className="input-hint">
            Nyaya AI is an AI assistant and may produce inaccurate information. 
            Verify with original legal texts.
          </div>
        </div>
      </div>

      {/* Copied toast */}
      {showCopied && (
        <div className="copied-toast">✓ Copied to clipboard</div>
      )}

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <UploadModal onClose={() => setIsUploadModalOpen(false)} />
      )}
    </div>
  );
}
