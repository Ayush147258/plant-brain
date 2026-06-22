'use client';

import React, { useState } from 'react';
import { mockDocuments } from '@/lib/mock-data/documents';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DataTable } from '@/components/dashboard/DataTable';
import { DocumentItem } from '@/types/dashboard';

export default function DocumentsPage() {
  const [search, setSearch] = useState('');
  
  const filteredDocs = mockDocuments.filter(d => 
    d.name.toLowerCase().includes(search.toLowerCase()) || 
    d.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {/* Summary Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '20px' }}>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Total Documents</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>12,842</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Categories</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>28</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Total Size</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>245.6 GB</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Last Updated</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>2 mins ago</div>
        </div>
      </div>

      <FilterBar 
        searchPlaceholder="Search document title, type, or content..."
        filters={['All Categories', 'All Types', 'All Time']}
        onSearchChange={setSearch}
      />

      <DataTable<DocumentItem> 
        data={filteredDocs}
        columns={[
          { 
            header: 'Document Name', 
            render: (doc) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#222', fontSize: '12.5px' }}>
                <i className="ti ti-file-text" style={{ color: '#e24b4a', fontSize: '16px' }}></i> {doc.name}
              </div>
            )
          },
          { header: 'Category', accessor: 'category' },
          { header: 'Type', render: (doc) => <span style={{ color: '#888', fontSize: '11px' }}>{doc.type}</span> },
          { header: 'Upload Date', accessor: 'uploadDate' },
          { header: 'Size', accessor: 'size' },
          { header: 'Actions', align: 'right', render: () => <i className="ti ti-dots" style={{ cursor: 'pointer', color: '#888' }}></i> }
        ]}
      />
    </div>
  );
}
