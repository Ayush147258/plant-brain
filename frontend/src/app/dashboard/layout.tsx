'use client';

import React from 'react';
import './dashboard.css';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Topbar } from '@/components/dashboard/Topbar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.7.0/tabler-icons.min.css" />
      <div className="dashboard-root">
        <Sidebar />
        <div className="main">
          <Topbar />
          <div className="content">
            {children}
          </div>
        </div>
      </div>
    </>
  );
}
