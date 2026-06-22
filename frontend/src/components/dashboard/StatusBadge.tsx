import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  let bg = '#f0f0ec';
  let color = '#555';

  switch (status) {
    case 'Active':
    case 'Compliant':
    case 'Documented':
      bg = '#e1f5ee';
      color = '#0f6e56';
      break;
    case 'Maintenance':
    case 'Pending':
    case 'In Progress':
    case 'Pending Review':
    case 'At Risk':
      bg = '#faeeda';
      color = '#854f0b';
      break;
    case 'Offline':
    case 'Non-Compliant':
      bg = '#fcebeb';
      color = '#a32d2d';
      break;
  }

  return (
    <span style={{
      fontSize: '10px',
      padding: '2px 8px',
      borderRadius: '4px',
      fontWeight: 500,
      background: bg,
      color: color,
    }}>
      {status}
    </span>
  );
}
