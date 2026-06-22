'use client';

import React, { useState } from 'react';
import { mockIntegrations } from '@/lib/mock-data/integrations';
import { IntegrationItem } from '@/types/dashboard';

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<IntegrationItem[]>(mockIntegrations);

  const toggleConnection = (id: string) => {
    setIntegrations(integrations.map(int => {
      if (int.id === id) {
        return {
          ...int,
          status: int.status === 'Connected' ? 'Not Connected' : 'Connected',
          lastSync: int.status === 'Connected' ? '-' : 'Just now'
        };
      }
      return int;
    }));
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
      {integrations.map((item) => (
        <div key={item.id} style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: `${item.color}15`, color: item.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
              <i className={`ti ${item.icon}`}></i>
            </div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#111' }}>{item.name}</div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', marginBottom: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: item.status === 'Connected' ? '#1d9e75' : '#ccc' }}></div>
            <span style={{ color: item.status === 'Connected' ? '#1d9e75' : '#888', fontWeight: 500 }}>{item.status}</span>
          </div>

          <div style={{ fontSize: '11px', color: '#888', marginBottom: '20px' }}>
            Last sync: {item.lastSync}
          </div>

          <div style={{ borderTop: '0.5px solid #eee', paddingTop: '16px', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '12px', color: '#534ab7', fontWeight: 500, cursor: 'pointer' }}>
              {item.status === 'Connected' ? 'Sync Settings' : 'Setup Integration'}
            </span>
            <span 
              onClick={() => toggleConnection(item.id)}
              style={{ fontSize: '12px', color: item.status === 'Connected' ? '#e24b4a' : '#1d9e75', cursor: 'pointer' }}
            >
              {item.status === 'Connected' ? 'Disconnect' : 'Connect'}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
