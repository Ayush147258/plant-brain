import React from 'react';

interface FilterBarProps {
  searchPlaceholder?: string;
  filters: string[];
  onSearchChange?: (val: string) => void;
  onFilterChange?: (filterIndex: number, val: string) => void;
  showFiltersButton?: boolean;
}

export function FilterBar({ searchPlaceholder = "Search...", filters, onSearchChange, onFilterChange, showFiltersButton = true }: FilterBarProps) {
  return (
    <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', alignItems: 'center' }}>
      <div style={{ position: 'relative', flex: 1 }}>
        <i className="ti ti-search" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#aaa' }}></i>
        <input 
          type="text" 
          placeholder={searchPlaceholder}
          onChange={(e) => onSearchChange?.(e.target.value)}
          style={{ width: '100%', padding: '9px 12px 9px 36px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '13px', outline: 'none' }}
        />
      </div>
      {filters.map((filterName, idx) => (
        <select key={idx} onChange={(e) => onFilterChange?.(idx, e.target.value)} style={{ padding: '0 12px', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '12.5px', background: '#fff', color: '#444', outline: 'none', height: '36px' }}>
          <option>{filterName}</option>
        </select>
      ))}
      {showFiltersButton && (
        <button style={{ padding: '0 16px', height: '36px', background: '#fff', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <i className="ti ti-filter"></i> Filters
        </button>
      )}
    </div>
  );
}
