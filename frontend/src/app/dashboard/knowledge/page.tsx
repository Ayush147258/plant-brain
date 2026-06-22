'use client';

import React, { useState } from 'react';
import { mockKnowledge } from '@/lib/mock-data/knowledge';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { KnowledgeItem } from '@/types/dashboard';

export default function KnowledgeCapturePage() {
  const [search, setSearch] = useState('');
  
  const filteredKnowledge = mockKnowledge.filter(k => 
    k.title.toLowerCase().includes(search.toLowerCase()) || 
    k.expert.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '20px' }}>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Total Knowledge Items</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>156</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>This Week</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>22</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>This Month</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>56</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Total Experts</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>18</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid #ddd', marginBottom: '16px' }}>
        <div style={{ paddingBottom: '10px', borderBottom: '2px solid #534ab7', color: '#534ab7', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>All Knowledge</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Voice Captures</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Documented</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Pending Review</div>
      </div>

      <FilterBar 
        searchPlaceholder="Search knowledge items..."
        filters={['All Types', 'All Experts', 'All Time']}
        onSearchChange={setSearch}
      />

      <DataTable<KnowledgeItem>
        data={filteredKnowledge}
        columns={[
          { 
            header: 'Title', 
            render: (k) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#444', fontSize: '12.5px' }}>
                <i className={k.type === 'Voice' ? 'ti ti-microphone' : 'ti ti-file-text'} style={{ color: k.type === 'Voice' ? '#378add' : '#1d9e75', fontSize: '16px' }}></i>
                {k.title}
              </div>
            ) 
          },
          { header: 'Type', accessor: 'type' },
          { header: 'Expert', accessor: 'expert' },
          { header: 'Captured On', accessor: 'capturedOn' },
          { header: 'Status', render: (k) => <StatusBadge status={k.status} /> }
        ]}
      />
    </div>
  );
}
