import React, { ReactNode } from 'react';

interface Column<T> {
  header: string;
  accessor?: keyof T;
  render?: (item: T) => ReactNode;
  align?: 'left' | 'right' | 'center';
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (item: T) => void;
}

export function DataTable<T>({ data, columns, onRowClick }: DataTableProps<T>) {
  return (
    <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead>
          <tr style={{ background: '#f9f9f7', borderBottom: '0.5px solid #e5e5e0', color: '#888', fontSize: '11px' }}>
            {columns.map((col, idx) => (
              <th key={idx} style={{ padding: '12px 16px', fontWeight: 500, textAlign: col.align || 'left' }}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr 
              key={rowIdx} 
              onClick={() => onRowClick?.(row)}
              style={{ 
                borderBottom: rowIdx < data.length - 1 ? '0.5px solid #f0f0ec' : 'none',
                cursor: onRowClick ? 'pointer' : 'default',
                transition: 'background 0.1s'
              }}
              onMouseEnter={(e) => { if(onRowClick) e.currentTarget.style.background = '#fafafa'; }}
              onMouseLeave={(e) => { if(onRowClick) e.currentTarget.style.background = 'transparent'; }}
            >
              {columns.map((col, colIdx) => (
                <td key={colIdx} style={{ padding: '12px 16px', fontSize: '12px', color: '#555', textAlign: col.align || 'left' }}>
                  {col.render ? col.render(row) : (col.accessor ? String(row[col.accessor]) : null)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
