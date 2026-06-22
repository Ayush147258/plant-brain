'use client';

import React, { useState } from 'react';
import { mockEquipment } from '@/lib/mock-data/equipment';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { EquipmentItem } from '@/types/dashboard';

export default function EquipmentPage() {
  const [search, setSearch] = useState('');
  
  const filteredEquipment = mockEquipment.filter(e => 
    e.name.toLowerCase().includes(search.toLowerCase()) || 
    e.id.toLowerCase().includes(search.toLowerCase()) ||
    e.type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '20px' }}>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Total Equipment</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>2,153</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Critical Equipment</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>156</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Active Equipment</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>1,897</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Under Maintenance</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>98</div>
        </div>
      </div>

      <FilterBar 
        searchPlaceholder="Search equipment by name, ID, or type..."
        filters={['All Types', 'All Status', 'Zone']}
        onSearchChange={setSearch}
      />

      <DataTable<EquipmentItem>
        data={filteredEquipment}
        columns={[
          { header: 'Equipment ID', render: (eq) => <span style={{ color: '#222', fontWeight: 500 }}>{eq.id}</span> },
          { header: 'Name', render: (eq) => <span style={{ color: '#444', fontSize: '12.5px' }}>{eq.name}</span> },
          { header: 'Type', accessor: 'type' },
          { header: 'Zone', accessor: 'zone' },
          { header: 'Status', render: (eq) => <StatusBadge status={eq.status} /> },
          { header: 'Last Maintenance', accessor: 'lastMaintenance' }
        ]}
      />
    </div>
  );
}
