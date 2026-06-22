'use client';

import React from 'react';
import { usePathname } from 'next/navigation';

export function Topbar() {
  const pathname = usePathname();

  const getPageMeta = (path: string) => {
    switch(path) {
      case '/dashboard': return { title: 'Good morning, Amit 👋', sub: "Here's what's happening at your plant today.", button: null };
      case '/dashboard/ask': return { title: 'Ask PlantBrain', sub: 'Your AI assistant for plant knowledge', button: null };
      case '/dashboard/documents': return { title: 'Documents', sub: 'All plant documents in one place', button: 'Upload Document' };
      case '/dashboard/equipment': return { title: 'Equipment', sub: 'All equipment and assets tracked', button: 'Add Equipment' };
      case '/dashboard/work-orders': return { title: 'Work Orders', sub: 'Manage and track all work orders', button: 'Create Work Order' };
      case '/dashboard/compliance': return { title: 'Compliance', sub: 'Track compliance and open findings', button: 'Generate Report' };
      case '/dashboard/reports': return { title: 'Reports & Analytics', sub: 'Insights and analytics for your plant', button: 'Export Report' };
      case '/dashboard/knowledge': return { title: 'Knowledge Capture', sub: 'Capture and preserve expert knowledge', button: 'Capture Knowledge' };
      case '/dashboard/alerts': return { title: 'Alerts', sub: 'System alerts and notifications', button: null };
      case '/dashboard/integrations': return { title: 'Integrations', sub: 'Connect with your existing systems', button: 'Add Integrations' };
      case '/dashboard/settings': return { title: 'Settings', sub: 'Manage your account and preferences', button: null };
      default: return { title: 'Dashboard', sub: '', button: null };
    }
  };

  const meta = getPageMeta(pathname);

  return (
    <header className="topbar">
      <div className="greeting">
        <h2>{meta.title}</h2>
        <p>{meta.sub}</p>
      </div>
      
      {pathname === '/dashboard' ? (
        <div className="search-wrap">
          <input placeholder="Ask anything about your plant..." />
          <span className="kbd">Ctrl + K</span>
          <i className="ti ti-search"></i>
        </div>
      ) : null}

      <div className="topbar-icons">
        <div className="icon-btn"><i className="ti ti-help-circle"></i></div>
        <div className="icon-btn"><i className="ti ti-bell"></i><span className="notif-dot">12</span></div>
        <div className="plant-tag"><i className="ti ti-building-factory-2"></i> Shakti Steel Plant <i className="ti ti-chevron-down" style={{fontSize:'12px'}}></i></div>
        {meta.button && (
          <button className="btn-primary">
            <i className="ti ti-plus"></i> {meta.button}
          </button>
        )}
      </div>
    </header>
  );
}
