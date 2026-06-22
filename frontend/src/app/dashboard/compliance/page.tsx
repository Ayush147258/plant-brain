'use client';

import React, { useState } from 'react';
import { mockCompliance } from '@/lib/mock-data/compliance';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { ComplianceRequirement } from '@/types/dashboard';

export default function CompliancePage() {
  const [search, setSearch] = useState('');
  
  const filteredReqs = mockCompliance.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    c.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '20px' }}>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Overall Compliance Score</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#1d9e75' }}>94%</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Requirements</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>92</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Compliant</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>76</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>At Risk</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>6</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid #ddd', marginBottom: '16px' }}>
        <div style={{ paddingBottom: '10px', borderBottom: '2px solid #534ab7', color: '#534ab7', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>All Requirements</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>OISD Compliance</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Factory Act</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>PESO Regulations</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Environmental</div>
      </div>

      <FilterBar 
        searchPlaceholder="Search requirements..."
        filters={['All Categories', 'All Status']}
        onSearchChange={setSearch}
      />

      <DataTable<ComplianceRequirement>
        data={filteredReqs}
        columns={[
          { header: 'Requirement', render: (c) => <span style={{ color: '#444', fontSize: '12.5px' }}>{c.name}</span> },
          { header: 'Category', accessor: 'category' },
          { header: 'Status', render: (c) => <StatusBadge status={c.status} /> },
          { header: 'Last Check', accessor: 'lastCheck' },
          { header: 'Next Due', accessor: 'nextDue' }
        ]}
      />
    </div>
  );
}
