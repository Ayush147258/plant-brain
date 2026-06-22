'use client';

import React, { useState } from 'react';
import { mockAlerts } from '@/lib/mock-data/alerts';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DataTable } from '@/components/dashboard/DataTable';
import { AlertItem } from '@/types/dashboard';

export default function AlertsPage() {
  const [search, setSearch] = useState('');
  const [alerts, setAlerts] = useState<AlertItem[]>(mockAlerts);
  
  const filteredAlerts = alerts.filter(a => 
    a.text.toLowerCase().includes(search.toLowerCase()) || 
    a.type.toLowerCase().includes(search.toLowerCase())
  );

  const getSeverityColor = (s: string) => {
    if (s === 'Critical') return '#e24b4a';
    if (s === 'High') return '#ef9f27';
    if (s === 'Medium') return '#ba7517';
    return '#378add';
  };

  const getSeverityIcon = (s: string) => {
    if (s === 'Critical') return 'ti-alert-triangle';
    if (s === 'High') return 'ti-alert-circle';
    if (s === 'Medium') return 'ti-alert-circle';
    return 'ti-info-circle';
  };

  const markAllRead = () => {
    setAlerts(alerts.map(a => ({ ...a, status: 'Read' })));
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid #ddd', marginBottom: '16px' }}>
        <div style={{ paddingBottom: '10px', borderBottom: '2px solid #534ab7', color: '#534ab7', fontSize: '13px', fontWeight: 500, cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span>All Alerts</span>
          <span style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>{alerts.length}</span>
        </div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span>Critical</span>
          <span style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>{alerts.filter(a => a.severity === 'Critical').length}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <FilterBar 
            searchPlaceholder="Search alerts..."
            filters={['All Types', 'All Status']}
            onSearchChange={setSearch}
            showFiltersButton={false}
          />
        </div>
        <div onClick={markAllRead} style={{ fontSize: '12px', color: '#378add', cursor: 'pointer', marginLeft: 'auto', marginBottom: '16px' }}>
          mark all as read
        </div>
      </div>

      <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f9f9f7', borderBottom: '0.5px solid #e5e5e0', color: '#888', fontSize: '11px' }}>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>Alert</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>Type</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>Severity</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>Time</th>
              <th style={{ padding: '12px 16px', fontWeight: 500 }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.map((al, idx) => (
              <tr key={idx} style={{ borderBottom: idx < filteredAlerts.length - 1 ? '0.5px solid #f0f0ec' : 'none', background: al.status === 'New' ? '#fff' : '#fafafa' }}>
                <td style={{ padding: '12px 16px', fontSize: '12.5px', color: '#444', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <i className={`ti ${getSeverityIcon(al.severity)}`} style={{ color: getSeverityColor(al.severity), fontSize: '16px' }}></i>
                  {al.text}
                </td>
                <td style={{ padding: '12px 16px', fontSize: '12px', color: '#555' }}>{al.type}</td>
                <td style={{ padding: '12px 16px', fontSize: '12px', color: getSeverityColor(al.severity), fontWeight: 500 }}>{al.severity}</td>
                <td style={{ padding: '12px 16px', fontSize: '12px', color: '#555' }}>{al.time}</td>
                <td style={{ padding: '12px 16px', fontSize: '12px', fontWeight: 500, color: al.status === 'New' ? '#111' : '#888' }}>{al.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
