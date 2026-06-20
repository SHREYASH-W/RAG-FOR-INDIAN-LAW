'use client';

import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (question) => {
    const textToSend = question || input;
    if (!textToSend.trim()) return;

    // Add user message
    const userMsg = { role: 'user', content: textToSend };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    // Add typing indicator
    setMessages(prev => [...prev, { role: 'ai', content: 'typing' }]);

    try {
      const res = await fetch('http://localhost:8000/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: textToSend }),
      });

      const data = await res.json();
      
      // Replace typing indicator with actual response
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { 
          role: 'ai', 
          content: data.answer || "Sorry, I couldn't generate an answer.",
          sources: data.sources || []
        };
        return newMsgs;
      });
    } catch (error) {
      console.error('Failed to get answer:', error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { 
          role: 'ai', 
          content: "Sorry, there was an error connecting to the server. Please ensure the backend is running." 
        };
        return newMsgs;
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

  const sampleQuestions = [
    "What are the fundamental rights under the Indian Constitution?",
    "Explain the procedure for arrest under Bharatiya Nagarik Suraksha Sanhita.",
    "What is the penalty for cyber terrorism under the IT Act?",
    "Can a person be forced to be a witness against himself?"
  ];

  return (
    <div className="main-content">
      <header className="chat-header">
        <div className="chat-header-title">
          <div className="header-dot"></div>
          Nyaya AI Engine
        </div>
        <div className="header-badge">RAG Active</div>
      </header>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-emblem">⚖️</div>
            <h1 className="welcome-heading">Indian Law Assistant</h1>
            <p className="welcome-subheading">
              Ask any question about the Indian Constitution, BNS, IT Act, and more. 
              Powered by advanced AI and dynamic RAG.
            </p>
            
            <div className="sample-questions">
              {sampleQuestions.map((q, i) => (
                <button 
                  key={i} 
                  className="sample-question"
                  onClick={() => handleSend(q)}
                >
                  <span className="sample-question-icon">🔍</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <MessageBubble key={idx} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            className="chat-input"
            placeholder="Ask a legal question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
          />
          <button 
            className="send-button"
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
          >
            ↗
          </button>
        </div>
        <div className="input-hint">
          Nyaya AI can make mistakes. Always verify with original legal texts.
        </div>
      </div>
    </div>
  );
}
