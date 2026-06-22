'use client';

import React, { useState } from 'react';
import { mockWorkOrders } from '@/lib/mock-data/work-orders';
import { FilterBar } from '@/components/dashboard/FilterBar';
import { DataTable } from '@/components/dashboard/DataTable';
import { StatusBadge } from '@/components/dashboard/StatusBadge';
import { WorkOrder } from '@/types/dashboard';

export default function WorkOrdersPage() {
  const [search, setSearch] = useState('');
  
  const filteredOrders = mockWorkOrders.filter(w => 
    w.title.toLowerCase().includes(search.toLowerCase()) || 
    w.id.toLowerCase().includes(search.toLowerCase())
  );

  const getPriorityColor = (p: string) => {
    if (p === 'High') return '#e24b4a';
    if (p === 'Medium') return '#ef9f27';
    return '#378add';
  };

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px', marginBottom: '20px' }}>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>All Orders</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#111' }}>324</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Open</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#378add' }}>160</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>In Progress</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#1d9e75' }}>98</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Pending</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#ef9f27' }}>42</div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '16px' }}>
          <div style={{ fontSize: '11px', color: '#888', marginBottom: '4px' }}>Closed</div>
          <div style={{ fontSize: '20px', fontWeight: 600, color: '#888' }}>24</div>
        </div>
      </div>

      <FilterBar 
        searchPlaceholder="Search work orders..."
        filters={['All Priority', 'All Time']}
        onSearchChange={setSearch}
      />

      <DataTable<WorkOrder>
        data={filteredOrders}
        columns={[
          { header: 'WO Number', render: (w) => <span style={{ color: '#222', fontWeight: 500 }}>{w.id}</span> },
          { header: 'Title', render: (w) => <span style={{ color: '#444', fontSize: '12.5px' }}>{w.title}</span> },
          { header: 'Type', accessor: 'type' },
          { header: 'Priority', render: (w) => <span style={{ color: getPriorityColor(w.priority), fontWeight: 500 }}>{w.priority}</span> },
          { header: 'Status', render: (w) => <StatusBadge status={w.status} /> },
          { header: 'Assigned To', accessor: 'assignedTo' },
          { header: 'Due Date', accessor: 'dueDate' }
        ]}
      />
    </div>
  );
}
