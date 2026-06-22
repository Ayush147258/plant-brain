'use client';

import React, { useState } from 'react';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('Profile');

  const settingsNav = [
    { name: "Profile" },
    { name: "Plant Settings" },
    { name: "User Management" },
    { name: "Roles & Permissions" },
    { name: "Notification Settings" },
    { name: "AI Settings" },
    { name: "Security" },
    { name: "Backup & Sync" },
    { name: "API Settings" },
  ];

  return (
    <div style={{ display: 'flex', gap: '30px', height: '100%' }}>
      {/* Settings Sidebar */}
      <div style={{ width: '220px', flexShrink: 0, borderRight: '0.5px solid #ddd', paddingRight: '20px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {settingsNav.map((nav, idx) => {
            const isActive = activeTab === nav.name;
            return (
              <div 
                key={idx} 
                onClick={() => setActiveTab(nav.name)}
                style={{ 
                  padding: '10px 14px', 
                  borderRadius: '8px', 
                  fontSize: '12.5px', 
                  cursor: 'pointer',
                  background: isActive ? '#eeedfe' : 'transparent',
                  color: isActive ? '#534ab7' : '#555',
                  fontWeight: isActive ? 500 : 400
                }}
              >
                {nav.name}
              </div>
            );
          })}
        </div>
      </div>

      {/* Settings Content */}
      <div style={{ flex: 1, maxWidth: '600px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#111', marginBottom: '24px' }}>
          {activeTab === 'Profile' ? 'Profile Information' : `${activeTab} Configuration`}
        </h3>
        
        {activeTab === 'Profile' ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#888', marginBottom: '6px' }}>Full Name</label>
                <input type="text" defaultValue="Amit Sharma" style={{ width: '100%', padding: '10px 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#888', marginBottom: '6px' }}>Email</label>
                <input type="email" defaultValue="amit.sharma@shaktisteel.com" style={{ width: '100%', padding: '10px 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa', color: '#888' }} readOnly />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#888', marginBottom: '6px' }}>Phone</label>
                <input type="text" defaultValue="+91 98765 43210" style={{ width: '100%', padding: '10px 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none' }} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#888', marginBottom: '6px' }}>Role</label>
                <input type="text" defaultValue="Plant Manager" style={{ width: '100%', padding: '10px 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa', color: '#888' }} readOnly />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#888', marginBottom: '6px' }}>Language</label>
                <select style={{ width: '100%', padding: '10px 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fff' }}>
                  <option>English</option>
                  <option>Hindi</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#888', marginBottom: '6px' }}>Timezone</label>
                <select style={{ width: '100%', padding: '10px 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fff' }}>
                  <option>Asia/Kolkata</option>
                  <option>UTC</option>
                </select>
              </div>
            </div>

            <div style={{ borderTop: '0.5px solid #eee', paddingTop: '24px', display: 'flex', gap: '12px' }}>
              <button style={{ padding: '10px 20px', background: '#534ab7', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>
                Save Changes
              </button>
              <button style={{ padding: '10px 20px', background: '#fff', color: '#534ab7', border: '1px solid #534ab7', borderRadius: '8px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>
                Change Password
              </button>
            </div>
          </>
        ) : (
          <div style={{ color: '#888', fontSize: '13px' }}>
            Settings for {activeTab} will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
