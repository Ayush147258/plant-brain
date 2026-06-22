'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: 'Dashboard', icon: 'ti-layout-dashboard', path: '/dashboard' },
    { name: 'Ask PlantBrain', icon: 'ti-message-circle', path: '/dashboard/ask' },
    { name: 'Documents', icon: 'ti-files', path: '/dashboard/documents' },
    { name: 'Equipment', icon: 'ti-settings-2', path: '/dashboard/equipment' },
    { name: 'Work Orders', icon: 'ti-clipboard-list', path: '/dashboard/work-orders' },
    { name: 'Compliance', icon: 'ti-shield-check', path: '/dashboard/compliance' },
    { name: 'Reports & Analytics', icon: 'ti-chart-bar', path: '/dashboard/reports' },
    { name: 'Knowledge Capture', icon: 'ti-microphone', path: '/dashboard/knowledge' },
    { name: 'Alerts', icon: 'ti-bell', path: '/dashboard/alerts', badge: 12 },
    { name: 'Integrations', icon: 'ti-plug', path: '/dashboard/integrations' },
    { name: 'Settings', icon: 'ti-settings', path: '/dashboard/settings' },
  ];

  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-icon"><i className="ti ti-brain"></i></div>
        <div>
          <div className="logo-title">PlantBrain</div>
          <div className="logo-sub">Know More. Downtime Less.</div>
        </div>
      </div>
      <nav className="nav">
        {navItems.map(item => {
          const isActive = pathname === item.path;
          return (
            <Link key={item.path} href={item.path} className={`nav-item ${isActive ? 'active' : ''}`}>
              <i className={`ti ${item.icon}`}></i> {item.name}
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </Link>
          );
        })}
      </nav>
      <div className="user-row">
        <div className="user-avatar">AS</div>
        <div>
          <div className="user-name">Amit Sharma</div>
          <div className="user-role">Plant Manager</div>
        </div>
        <i className="ti ti-chevron-down" style={{marginLeft:'auto', fontSize:'14px', color:'#666'}}></i>
      </div>
    </aside>
  );
}
