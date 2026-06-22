'use client';

import React, { useState } from 'react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function AskPlantBrain() {
  const [query, setQuery] = useState('');
  const [chat, setChat] = useState<ChatMessage[]>([]);

  const suggestions = [
    "What is the maintenance procedure for P-201 pump?",
    "Which equipment in Zone 3 shares a process line with P-201?",
    "Show me the last 5 breakdowns of heat exchanger E-105",
    "What are the compliance requirements for OISD regulation 2022?"
  ];

  const recents = [
    { title: "P-201 Pump maintenance procedure", time: "2 mins ago" },
    { title: "Zone 3 equipment line mapping", time: "15 mins ago" },
    { title: "Heat exchanger E-105 breakdown history", time: "1 hour ago" }
  ];

  const handleSend = (text: string) => {
    if (!text.trim()) return;
    setChat([...chat, { role: 'user', content: text }]);
    setQuery('');
    
    // Mock AI response
    setTimeout(() => {
      setChat(prev => [...prev, { 
        role: 'assistant', 
        content: `Based on the latest documentation, here is the answer regarding "${text}". \n\nThe P-201 pump requires a visual inspection every 7 days and a full seal replacement every 6 months. For OISD compliance, ensure the clearance area is strictly maintained.` 
      }]);
    }, 600);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      
      {chat.length === 0 ? (
        <>
          <div style={{ textAlign: 'center', marginBottom: '40px', marginTop: '40px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 600, color: '#111', marginBottom: '8px' }}>
              Hello Amit! 👋
            </h1>
            <p style={{ fontSize: '15px', color: '#555' }}>
              How can I help you today?
            </p>
          </div>

          <div style={{ position: 'relative', marginBottom: '30px' }}>
            <textarea 
              placeholder="Ask anything about your plant, equipment, procedures, or compliance..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(query); } }}
              style={{
                width: '100%', height: '110px', padding: '16px 20px', paddingBottom: '40px',
                borderRadius: '12px', border: '1px solid #ddd', fontSize: '14px', resize: 'none',
                outline: 'none', background: '#fff', boxShadow: '0 4px 14px rgba(0,0,0,0.03)'
              }}
            />
            <div style={{ position: 'absolute', bottom: '16px', left: '20px', right: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '11px', color: '#aaa', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <i className="ti ti-info-circle"></i> PlantBrain uses your plant's data
              </span>
              <button 
                onClick={() => handleSend(query)}
                style={{ 
                  background: '#534ab7', color: '#fff', border: 'none', borderRadius: '8px', 
                  padding: '6px 12px', fontSize: '12px', fontWeight: 500, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '6px'
                }}>
                Ask <i className="ti ti-send" style={{ fontSize: '14px' }}></i>
              </button>
            </div>
          </div>

          <div style={{ marginBottom: '40px' }}>
            <div style={{ fontSize: '12px', color: '#888', marginBottom: '12px' }}>Try asking:</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {suggestions.map((s, idx) => (
                <button 
                  key={idx}
                  onClick={() => handleSend(s)}
                  style={{
                    textAlign: 'left', background: '#eeedfe', color: '#534ab7', 
                    border: '1px solid rgba(83, 74, 183, 0.15)', borderRadius: '8px', 
                    padding: '12px 16px', fontSize: '13px', cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="panel" style={{ background: 'transparent', border: 'none', padding: 0 }}>
            <div className="panel-hdr" style={{ marginBottom: '16px' }}>
              <span className="panel-title" style={{ fontSize: '12px', color: '#888', fontWeight: 400 }}>Recent Conversations</span>
              <span className="view-all">View all</span>
            </div>
            <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', overflow: 'hidden' }}>
              {recents.map((item, idx) => (
                <div key={idx} style={{ 
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 16px', 
                  borderBottom: idx < recents.length - 1 ? '0.5px solid #f0f0ec' : 'none',
                  cursor: 'pointer'
                }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#f1efe8', color: '#5f5e5a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }}>
                    <i className="ti ti-message-circle"></i>
                  </div>
                  <div style={{ flex: 1, fontSize: '13px', color: '#222' }}>{item.title}</div>
                  <div style={{ fontSize: '11px', color: '#999' }}>{item.time}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Chat History */}
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '10px', marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {chat.map((msg, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '16px', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
                <div style={{ 
                  width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0,
                  background: msg.role === 'user' ? '#378add' : '#534ab7', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' 
                }}>
                  {msg.role === 'user' ? 'AS' : <i className="ti ti-brain"></i>}
                </div>
                <div style={{ 
                  background: msg.role === 'user' ? '#e6f1fb' : '#fff',
                  border: msg.role === 'user' ? 'none' : '0.5px solid #ddd',
                  padding: '16px', borderRadius: '12px', fontSize: '13px', color: '#333',
                  lineHeight: 1.5, maxWidth: '80%', whiteSpace: 'pre-wrap'
                }}>
                  {msg.content}
                  {msg.role === 'assistant' && (
                    <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '0.5px solid #eee', display: 'flex', gap: '8px' }}>
                      <div style={{ fontSize: '10px', color: '#888' }}>Sources:</div>
                      <span style={{ fontSize: '10px', background: '#f5f5f3', padding: '2px 6px', borderRadius: '4px', border: '0.5px solid #e5e5e0' }}>P-201 Manual.pdf</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Sticky Input for Active Chat */}
          <div style={{ position: 'relative' }}>
            <input 
              placeholder="Ask a follow-up question..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSend(query); }}
              style={{
                width: '100%', padding: '16px 48px 16px 20px',
                borderRadius: '30px', border: '1px solid #ddd', fontSize: '14px',
                outline: 'none', background: '#fff', boxShadow: '0 4px 14px rgba(0,0,0,0.03)'
              }}
            />
            <button 
              onClick={() => handleSend(query)}
              style={{ 
                position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)',
                background: '#534ab7', color: '#fff', border: 'none', borderRadius: '50%', 
                width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
              }}>
              <i className="ti ti-send"></i>
            </button>
          </div>
        </>
      )}

    </div>
  );
}
