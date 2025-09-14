import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../services/api';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = { role: 'user', content: inputMessage };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(inputMessage, messages);
      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.speak,
        actions: response.data.actions || []
      };
      setMessages([...newMessages, assistantMessage]);
    } catch (error) {
      const errorMessage = { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.',
        isError: true
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div>
      <h1>AI Nutrition Coach</h1>
      <p className="mb-20">Chat with your personal nutrition coach</p>

      <div className="card" style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
        <div className="flex flex-between" style={{ marginBottom: '20px' }}>
          <h3>Chat</h3>
          <button onClick={clearChat} className="btn btn-secondary" style={{ fontSize: '12px' }}>
            Clear Chat
          </button>
        </div>

        {/* Messages */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '10px', 
          background: '#f8f9fa',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#666', marginTop: '50px' }}>
              <h4>Welcome to your AI Nutrition Coach!</h4>
              <p>Ask me anything about nutrition, food logging, or your health goals.</p>
              <div style={{ marginTop: '20px', fontSize: '14px' }}>
                <p><strong>Try asking:</strong></p>
                <ul style={{ textAlign: 'left', display: 'inline-block' }}>
                  <li>"Log 2 eggs and 1 slice of toast"</li>
                  <li>"What should I eat for breakfast?"</li>
                  <li>"Set my goal to 2000 calories"</li>
                  <li>"Show me today's nutrition summary"</li>
                </ul>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} style={{ 
                marginBottom: '15px',
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div style={{
                  maxWidth: '70%',
                  padding: '10px 15px',
                  borderRadius: '18px',
                  background: message.role === 'user' ? '#007bff' : 'white',
                  color: message.role === 'user' ? 'white' : '#333',
                  border: message.isError ? '1px solid #dc3545' : '1px solid #ddd',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                  
                  {message.actions && message.actions.length > 0 && (
                    <div style={{ 
                      marginTop: '10px', 
                      padding: '8px', 
                      background: 'rgba(0,0,0,0.1)', 
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      <strong>Actions taken:</strong>
                      <ul style={{ margin: '5px 0 0 15px' }}>
                        {message.actions.map((action, i) => (
                          <li key={i}>{action.action}: {JSON.stringify(action.args)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'flex-start',
              marginBottom: '15px'
            }}>
              <div style={{
                padding: '10px 15px',
                borderRadius: '18px',
                background: 'white',
                border: '1px solid #ddd',
                boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{ 
                    width: '8px', 
                    height: '8px', 
                    background: '#007bff', 
                    borderRadius: '50%',
                    animation: 'pulse 1.5s infinite'
                  }}></div>
                  <div style={{ 
                    width: '8px', 
                    height: '8px', 
                    background: '#007bff', 
                    borderRadius: '50%',
                    animation: 'pulse 1.5s infinite 0.2s'
                  }}></div>
                  <div style={{ 
                    width: '8px', 
                    height: '8px', 
                    background: '#007bff', 
                    borderRadius: '50%',
                    animation: 'pulse 1.5s infinite 0.4s'
                  }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} className="flex gap-10">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask your nutrition coach..."
            style={{ flex: 1 }}
            disabled={loading}
          />
          <button 
            type="submit" 
            className="btn"
            disabled={loading || !inputMessage.trim()}
          >
            Send
          </button>
        </form>
      </div>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default Chat;
