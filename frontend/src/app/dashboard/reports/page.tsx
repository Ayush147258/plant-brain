'use client';

import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function ReportsPage() {
  const donutRef = useRef<HTMLCanvasElement>(null);
  const lineRef = useRef<HTMLCanvasElement>(null);
  const donutInst = useRef<Chart | null>(null);
  const lineInst = useRef<Chart | null>(null);

  useEffect(() => {
    if (donutRef.current) {
      if (donutInst.current) donutInst.current.destroy();
      donutInst.current = new Chart(donutRef.current, {
        type: 'doughnut',
        data: {
          datasets: [{
            data: [38, 25, 16, 21],
            backgroundColor: ['#378add', '#ef9f27', '#1d9e75', '#e5e5e0'],
            borderWidth: 0,
            hoverOffset: 4
          }]
        },
        options: { cutout: '70%', plugins: { legend: { display: false }, tooltip: { enabled: true } }, animation: { duration: 900 } }
      });
    }

    if (lineRef.current) {
      if (lineInst.current) lineInst.current.destroy();
      lineInst.current = new Chart(lineRef.current, {
        type: 'line',
        data: {
          labels: ['1 May', '5 May', '10 May', '15 May', '20 May', '25 May', '30 May'],
          datasets: [{
            data: [12, 19, 8, 25, 14, 10, 15],
            borderColor: '#534ab7',
            borderWidth: 2,
            tension: 0.4,
            pointBackgroundColor: '#fff',
            pointBorderColor: '#534ab7',
            pointRadius: 4,
          }]
        },
        options: {
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 10 }, color: '#aaa' } },
            y: { border: { display: false }, grid: { color: '#f0f0ec' }, ticks: { font: { size: 10 }, color: '#aaa' } }
          }
        }
      });
    }

    return () => {
      if (donutInst.current) donutInst.current.destroy();
      if (lineInst.current) lineInst.current.destroy();
    };
  }, []);

  return (
    <div>
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid #ddd', marginBottom: '16px' }}>
        <div style={{ paddingBottom: '10px', borderBottom: '2px solid #534ab7', color: '#534ab7', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>Overview</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Downtime Analysis</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Maintenance Analytics</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Compliance Analytics</div>
        <div style={{ paddingBottom: '10px', color: '#888', fontSize: '13px', cursor: 'pointer' }}>Custom Reports</div>
      </div>

      {/* Filter Bar */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', alignItems: 'center' }}>
        <button style={{ padding: '8px 16px', background: '#fff', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <i className="ti ti-calendar"></i> 01 May 2024 - 30 May 2024
        </button>
        <button style={{ padding: '8px 16px', background: '#fff', border: '0.5px solid #ddd', borderRadius: '8px', fontSize: '12.5px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <i className="ti ti-filter"></i> Filters
        </button>
        <button style={{ marginLeft: 'auto', padding: '8px 16px', background: '#e6f1fb', color: '#378add', border: 'none', borderRadius: '8px', fontSize: '12.5px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <i className="ti ti-download"></i> Export Report
        </button>
      </div>

      {/* Summary Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '20px' }}>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '20px', position: 'relative' }}>
          <div style={{ fontSize: '11.5px', color: '#888', marginBottom: '8px' }}>Total Downtime (hrs)</div>
          <div style={{ fontSize: '26px', fontWeight: 600, color: '#111', marginBottom: '4px' }}>156.8</div>
          <div style={{ fontSize: '11px', color: '#1d9e75', fontWeight: 500 }}><i className="ti ti-arrow-down-right"></i> 12% vs last month</div>
          <div style={{ position: 'absolute', top: '20px', right: '20px', width: '32px', height: '32px', background: '#e1f5ee', color: '#1d9e75', borderRadius: '8px', display: 'flex', alignItems: 'center', fontSize: '16px', justifyContent: 'center' }}><i className="ti ti-clock"></i></div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '20px', position: 'relative' }}>
          <div style={{ fontSize: '11.5px', color: '#888', marginBottom: '8px' }}>Unplanned Downtime (hrs)</div>
          <div style={{ fontSize: '26px', fontWeight: 600, color: '#111', marginBottom: '4px' }}>98.4</div>
          <div style={{ fontSize: '11px', color: '#e24b4a', fontWeight: 500 }}><i className="ti ti-arrow-up-right"></i> 8% vs last month</div>
          <div style={{ position: 'absolute', top: '20px', right: '20px', width: '32px', height: '32px', background: '#faeeda', color: '#ba7517', borderRadius: '8px', display: 'flex', alignItems: 'center', fontSize: '16px', justifyContent: 'center' }}><i className="ti ti-alert-triangle"></i></div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '20px', position: 'relative' }}>
          <div style={{ fontSize: '11.5px', color: '#888', marginBottom: '8px' }}>MTBF (hrs)</div>
          <div style={{ fontSize: '26px', fontWeight: 600, color: '#111', marginBottom: '4px' }}>245.6</div>
          <div style={{ fontSize: '11px', color: '#1d9e75', fontWeight: 500 }}><i className="ti ti-arrow-up-right"></i> 18% vs last month</div>
          <div style={{ position: 'absolute', top: '20px', right: '20px', width: '32px', height: '32px', background: '#e6f1fb', color: '#378add', borderRadius: '8px', display: 'flex', alignItems: 'center', fontSize: '16px', justifyContent: 'center' }}><i className="ti ti-activity"></i></div>
        </div>
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '20px', position: 'relative' }}>
          <div style={{ fontSize: '11.5px', color: '#888', marginBottom: '8px' }}>Maintenance Cost (₹)</div>
          <div style={{ fontSize: '26px', fontWeight: 600, color: '#111', marginBottom: '4px' }}>12.45L</div>
          <div style={{ fontSize: '11px', color: '#1d9e75', fontWeight: 500 }}><i className="ti ti-arrow-down-right"></i> 15% vs last month</div>
          <div style={{ position: 'absolute', top: '20px', right: '20px', width: '32px', height: '32px', background: '#eeedfe', color: '#534ab7', borderRadius: '8px', display: 'flex', alignItems: 'center', fontSize: '16px', justifyContent: 'center' }}><i className="ti ti-receipt-2"></i></div>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '10px' }}>
        
        {/* Donut Chart Panel */}
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>Downtime by Equipment</div>
            <div style={{ fontSize: '11px', color: '#378add', cursor: 'pointer' }}>View all</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <div style={{ width: '120px', height: '120px', flexShrink: 0 }}>
              <canvas ref={donutRef}></canvas>
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11.5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#444' }}><div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#378add' }}></div> P-201 Pump</div>
                <div style={{ color: '#888' }}>38% (54.5 hrs)</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11.5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#444' }}><div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef9f27' }}></div> E-105 Heat Exchanger</div>
                <div style={{ color: '#888' }}>25% (39.2 hrs)</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11.5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#444' }}><div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#1d9e75' }}></div> T-101 Turbine</div>
                <div style={{ color: '#888' }}>16% (25.1 hrs)</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11.5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#444' }}><div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#e5e5e0' }}></div> Others</div>
                <div style={{ color: '#888' }}>21% (32.9 hrs)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Line Chart Panel */}
        <div style={{ background: '#fff', border: '0.5px solid #e5e5e0', borderRadius: '10px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600 }}>Downtime Trend</div>
          </div>
          <div style={{ height: '180px', width: '100%' }}>
            <canvas ref={lineRef}></canvas>
          </div>
        </div>

      </div>
    </div>
  );
}
