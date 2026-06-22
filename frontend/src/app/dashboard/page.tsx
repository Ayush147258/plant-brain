'use client';

import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function DashboardPage() {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (chartRef.current) {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
      chartInstance.current = new Chart(chartRef.current, {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [160, 98, 42, 24],
            backgroundColor: ['#378add','#ef9f27','#ba7517','#1d9e75'],
            borderWidth: 0,
            hoverOffset: 4
          }]
        },
        options: {
          cutout: '68%',
          plugins: { legend: { display: false }, tooltip: { enabled: true } },
          animation: { duration: 900 }
        }
      });
    }
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, []);

  return (
    <>
      <div className="last-upd">Last updated: 2 mins ago &nbsp;<i className="ti ti-refresh" style={{fontSize:'12px', verticalAlign:'-1px'}}></i></div>

      {/* ── Stat Cards ── */}
      <div className="stat-row">
        <div className="stat-card">
          <div><div className="stat-label">Total Documents</div><div className="stat-val">12,842</div><div className="stat-sub c-green">↑ 245 this week</div></div>
          <div className="stat-icon ic-blue"><i className="ti ti-file-text"></i></div>
        </div>
        <div className="stat-card">
          <div><div className="stat-label">Equipment Tracked</div><div className="stat-val">2,153</div><div className="stat-sub c-green">↑ 18 this week</div></div>
          <div className="stat-icon ic-teal"><i className="ti ti-settings-2"></i></div>
        </div>
        <div className="stat-card">
          <div><div className="stat-label">Work Orders</div><div className="stat-val">324</div><div className="stat-sub c-orange">12 Pending</div></div>
          <div className="stat-icon ic-amber"><i className="ti ti-clipboard-list"></i></div>
        </div>
        <div className="stat-card">
          <div><div className="stat-label">Compliance Score</div><div className="stat-val">94%</div><div className="stat-sub c-green">↑ 3% vs last month</div></div>
          <div className="stat-icon ic-purple"><i className="ti ti-shield-check"></i></div>
        </div>
        <div className="stat-card">
          <div><div className="stat-label">Knowledge Captured</div><div className="stat-val">156</div><div className="stat-sub c-green">↑ 22 this week</div></div>
          <div className="stat-icon ic-gray"><i className="ti ti-microphone"></i></div>
        </div>
      </div>

      {/* ── Top 3 panels ── */}
      <div className="panels">
        {/* Recent Questions */}
        <div className="panel">
          <div className="panel-hdr"><span className="panel-title">Recent Questions</span><span className="view-all">View all</span></div>
          <div className="q-item">
            <div className="q-bubble"><i className="ti ti-message-circle"></i></div>
            <div className="q-text"><div className="q-main">What is the maintenance procedure for P-201 pump?</div><div className="q-meta">Equipment · P-201</div></div>
            <div className="q-time">2 mins ago</div>
          </div>
          <div className="q-item">
            <div className="q-bubble"><i className="ti ti-message-circle"></i></div>
            <div className="q-text"><div className="q-main">Which equipment in Zone 3 shares a process line with P-201?</div><div className="q-meta">Process · Line Mapping</div></div>
            <div className="q-time">15 mins ago</div>
          </div>
          <div className="q-item">
            <div className="q-bubble"><i className="ti ti-message-circle"></i></div>
            <div className="q-text"><div className="q-main">Show me the last 5 breakdowns of heat exchanger E-105</div><div className="q-meta">Maintenance · Breakdown History</div></div>
            <div className="q-time">+1 hour ago</div>
          </div>
          <div className="q-item">
            <div className="q-bubble"><i className="ti ti-message-circle"></i></div>
            <div className="q-text"><div className="q-main">What are the compliance requirements for OISD regulation 2022?</div><div className="q-meta">Compliance · OISD</div></div>
            <div className="q-time">2 hours ago</div>
          </div>
        </div>

        {/* Work Order Donut */}
        <div className="panel">
          <div className="panel-hdr"><span className="panel-title">Work Order Overview</span><span className="view-all">View all</span></div>
          <div className="donut-wrap">
            <div className="donut-canvas-wrap">
              <canvas ref={chartRef} id="donut" width="120" height="120"></canvas>
              <div id="donutCenter"><span className="dv">324</span><span className="dl">Total</span></div>
            </div>
            <div className="donut-legend">
              <div className="legend-item"><div className="dot" style={{background:'#378add'}}></div><span className="leg-label">Open</span><span className="leg-pct">160 (49%)</span></div>
              <div className="legend-item"><div className="dot" style={{background:'#ef9f27'}}></div><span className="leg-label">In Progress</span><span className="leg-pct">98 (30%)</span></div>
              <div className="legend-item"><div className="dot" style={{background:'#ba7517'}}></div><span className="leg-label">Pending</span><span className="leg-pct">42 (13%)</span></div>
              <div className="legend-item"><div className="dot" style={{background:'#1d9e75'}}></div><span className="leg-label">Closed</span><span className="leg-pct">24 (8%)</span></div>
            </div>
          </div>
        </div>

        {/* Compliance */}
        <div className="panel">
          <div className="panel-hdr"><span className="panel-title">Compliance Status</span><span className="view-all">View all</span></div>
          <div className="comp-item">
            <div className="comp-name"><i className="ti ti-file-certificate" style={{color:'#1d9e75', fontSize:'15px'}}></i> OISD Compliance</div>
            <span className="badge-ok">Compliant</span><span className="comp-score">15 / 16</span>
          </div>
          <div className="comp-item">
            <div className="comp-name"><i className="ti ti-building" style={{color:'#e24b4a', fontSize:'15px'}}></i> Factory Act</div>
            <span className="badge-ok">Compliant</span><span className="comp-score">28 / 30</span>
          </div>
          <div className="comp-item">
            <div className="comp-name"><i className="ti ti-alert-triangle" style={{color:'#ef9f27', fontSize:'15px'}}></i> PESO Regulations</div>
            <span className="badge-risk">At Risk</span><span className="comp-score">8 / 12</span>
          </div>
          <div className="comp-item">
            <div className="comp-name"><i className="ti ti-leaf" style={{color:'#639922', fontSize:'15px'}}></i> Environmental Norms</div>
            <span className="badge-ok">Compliant</span><span className="comp-score">12 / 14</span>
          </div>
          <div className="overall-row">
            <span className="overall-label">Overall Compliance Score</span>
            <span className="overall-val">94%</span>
          </div>
        </div>
      </div>

      {/* ── Bottom 3 panels ── */}
      <div className="panels">
        {/* Alerts */}
        <div className="panel">
          <div className="panel-hdr"><span className="panel-title">Recent Alerts</span><span className="view-all">View all</span></div>
          <div className="alert-item">
            <div className="alert-left"><div className="alert-ic ai-high"><i className="ti ti-alert-triangle"></i></div><span className="sev sh">High</span></div>
            <div className="alert-body"><div className="alert-title">Pressure relief valve PRV-302 inspection overdue</div><div className="alert-meta">Equipment · PRV-302</div></div>
            <div className="alert-time">10 mins ago</div>
          </div>
          <div className="alert-item">
            <div className="alert-left"><div className="alert-ic ai-medium"><i className="ti ti-alert-circle"></i></div><span className="sev sm">Medium</span></div>
            <div className="alert-body"><div className="alert-title">Procedure for E-105 is not aligned with latest OISD update</div><div className="alert-meta">Compliance · OISD</div></div>
            <div className="alert-time">1 hour ago</div>
          </div>
          <div className="alert-item">
            <div className="alert-left"><div className="alert-ic ai-medium"><i className="ti ti-alert-circle"></i></div><span className="sev sm">Medium</span></div>
            <div className="alert-body"><div className="alert-title">Vibration analysis recommended for P-301</div><div className="alert-meta">Predictive Maintenance</div></div>
            <div className="alert-time">2 hours ago</div>
          </div>
          <div className="alert-item">
            <div className="alert-left"><div className="alert-ic ai-low"><i className="ti ti-info-circle"></i></div><span className="sev sl">Low</span></div>
            <div className="alert-body"><div className="alert-title">New document uploaded: OEM Manual - Turbine T-101</div><div className="alert-meta">Documents</div></div>
            <div className="alert-time">3 hours ago</div>
          </div>
        </div>

        {/* Downtime bars */}
        <div className="panel">
          <div className="panel-hdr">
            <span className="panel-title">Top Equipment by Downtime <span style={{fontWeight:400, color:'#888', fontSize:'11px'}}>(This Month)</span></span>
            <span className="view-all">View all</span>
          </div>
          <div className="eq-hdr"><span>Equipment</span><span>Downtime (hrs)</span></div>
          <div className="eq-item"><div className="eq-name">P-201 Pump</div><div className="eq-bar-bg"><div className="eq-bar" style={{width:'100%', background:'#e24b4a'}}></div></div><div className="eq-val">18.6</div></div>
          <div className="eq-item"><div className="eq-name">E-105 Heat Exchanger</div><div className="eq-bar-bg"><div className="eq-bar" style={{width:'67%', background:'#ef9f27'}}></div></div><div className="eq-val">12.4</div></div>
          <div className="eq-item"><div className="eq-name">T-101 Turbine</div><div className="eq-bar-bg"><div className="eq-bar" style={{width:'47%', background:'#ef9f27'}}></div></div><div className="eq-val">8.7</div></div>
          <div className="eq-item"><div className="eq-name">C-301 Compressor</div><div className="eq-bar-bg"><div className="eq-bar" style={{width:'33%', background:'#378add'}}></div></div><div className="eq-val">6.1</div></div>
          <div className="eq-item"><div className="eq-name">P-301 Pump</div><div className="eq-bar-bg"><div className="eq-bar" style={{width:'23%', background:'#378add'}}></div></div><div className="eq-val">4.3</div></div>
        </div>

        {/* Knowledge Capture */}
        <div className="panel">
          <div className="panel-hdr"><span className="panel-title">Knowledge Capture Activity</span><span className="view-all">View all</span></div>
          <div className="kc-item">
            <div className="kc-ic"><i className="ti ti-microphone"></i></div>
            <div className="kc-text">Senior technician Rajesh Kumar captured knowledge on P-201 seal replacement</div>
            <div className="kc-time">2 hours ago</div>
          </div>
          <div className="kc-item">
            <div className="kc-ic"><i className="ti ti-microphone"></i></div>
            <div className="kc-text">Voice note converted: Troubleshooting guide for V-101 valve</div>
            <div className="kc-time">5 hours ago</div>
          </div>
          <div className="kc-item">
            <div className="kc-ic"><i className="ti ti-microphone"></i></div>
            <div className="kc-text">Maintenance best practice for lubrication of bearings</div>
            <div className="kc-time">1 day ago</div>
          </div>
          <div className="kc-stats">
            <div className="kc-stat"><div className="kc-stat-lbl">This Week</div><div className="kc-stat-val">22</div><div className="kc-stat-sub">↑ 15%</div></div>
            <div className="kc-stat"><div className="kc-stat-lbl">This Month</div><div className="kc-stat-val">156</div><div className="kc-stat-sub">↑ 28%</div></div>
            <div className="kc-stat"><div className="kc-stat-lbl">Total</div><div className="kc-stat-val">1,247</div><div className="kc-stat-sub">&nbsp;</div></div>
          </div>
        </div>
      </div>

      {/* ── Quick Actions ── */}
      <div className="section-lbl">Quick Actions</div>
      <div className="quick-row">
        <div className="quick-card"><div className="quick-ic ic-purple"><i className="ti ti-message-circle"></i></div><div className="quick-title">Ask a Question</div><div className="quick-sub">Get instant answers</div></div>
        <div className="quick-card"><div className="quick-ic ic-blue"><i className="ti ti-upload"></i></div><div className="quick-title">Upload Document</div><div className="quick-sub">Add to knowledge base</div></div>
        <div className="quick-card"><div className="quick-ic ic-amber"><i className="ti ti-clipboard-list"></i></div><div className="quick-title">Create Work Order</div><div className="quick-sub">Raise a new request</div></div>
        <div className="quick-card"><div className="quick-ic ic-teal"><i className="ti ti-shield-check"></i></div><div className="quick-title">Compliance Report</div><div className="quick-sub">Generate report</div></div>
        <div className="quick-card"><div className="quick-ic ic-gray"><i className="ti ti-microphone"></i></div><div className="quick-title">Capture Knowledge</div><div className="quick-sub">Record expert knowledge</div></div>
      </div>
    </>
  );
}
