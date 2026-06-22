import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  subColor?: 'green' | 'orange' | 'red';
  icon: string;
  iconBgColorClass?: string;
  subIcon?: string;
}

export function StatCard({ label, value, subValue, subColor = 'green', icon, iconBgColorClass, subIcon }: StatCardProps) {
  return (
    <div className="stat-card">
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-val">{value}</div>
        {subValue && (
          <div className={`stat-sub c-${subColor}`}>
            {subIcon && <i className={subIcon}></i>} {subValue}
          </div>
        )}
      </div>
      {iconBgColorClass ? (
        <div className={`stat-icon ${iconBgColorClass}`}>
          <i className={icon}></i>
        </div>
      ) : null}
    </div>
  );
}
