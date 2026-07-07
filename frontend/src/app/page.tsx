'use client';

import React from 'react';
import Link from 'next/link';
import { BadgeCheck, BrainCircuit, BriefcaseBusiness, ClipboardCheck, DraftingCompass, FileUp, Files, Gauge, Globe2, HardHat, Languages, MessageSquareText, Mic2, Network, Radar, SearchCheck, ShieldAlert, ShieldCheck, UserRoundX } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="landing-page">
      <style dangerouslySetInnerHTML={{ __html: `
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        :root{
          --ink:#0A0C10;--ink2:#1C2030;--slate:#64748B;--slate-light:#94A3B8;
          --surface:#F8F9FC;--border:rgba(30,40,70,0.1);--border-strong:rgba(30,40,70,0.18);
          --accent:#0057FF;--accent-glow:rgba(0,87,255,0.10);--teal:#00D4AA;
          --warn:#FF6B35;--white:#FFFFFF;
          --fd:'Space Grotesk',sans-serif;--fb:'Inter',sans-serif;--fm:'JetBrains Mono',monospace;
        }
        html{scroll-behavior:smooth}
        body{font-family:var(--fb);background:var(--white);color:var(--ink);line-height:1.6;-webkit-font-smoothing:antialiased}

        /* NAV */
        nav.custom-nav {position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 56px;height:66px;background:rgba(255,255,255,0.92);backdrop-filter:blur(14px);border-bottom:1px solid var(--border)}
        .nav-logo{display:flex;align-items:center;gap:10px;font-family:var(--fd);font-weight:700;font-size:19px;color:var(--ink);text-decoration:none}
        .logo-mark{width:34px;height:34px;background:var(--ink);border-radius:9px;display:flex;align-items:center;justify-content:center}
        .logo-mark svg{width:18px;height:18px}
        .nav-links{display:flex;align-items:center;gap:36px}
        .nav-links a{font-size:14px;color:var(--slate);text-decoration:none;transition:color .2s}
        .nav-links a:hover{color:var(--ink)}
        .nav-btn{background:var(--ink)!important;color:#fff!important;padding:9px 22px;border-radius:9px;font-weight:600!important;font-family:var(--fd)!important;transition:background .2s!important}
        .nav-btn:hover{background:var(--accent)!important}

        /* HERO */
        .hero{min-height:100vh;display:flex;align-items:center;padding:120px 56px 80px;background:var(--ink);position:relative;overflow:hidden}
        .hero-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(0,87,255,0.055) 1px,transparent 1px),linear-gradient(90deg,rgba(0,87,255,0.055) 1px,transparent 1px);background-size:52px 52px}
        .hero-glow1{position:absolute;top:-180px;right:-80px;width:680px;height:680px;background:radial-gradient(circle,rgba(0,87,255,0.16) 0%,transparent 70%);pointer-events:none}
        .hero-glow2{position:absolute;bottom:-80px;left:180px;width:380px;height:380px;background:radial-gradient(circle,rgba(0,212,170,0.09) 0%,transparent 70%);pointer-events:none}
        .hero-inner{max-width:1160px;margin:0 auto;position:relative;z-index:1;display:grid;grid-template-columns:1fr 1fr;gap:72px;align-items:center}
        .hero-pill{display:inline-flex;align-items:center;gap:8px;font-family:var(--fm);font-size:11px;letter-spacing:.12em;color:var(--teal);text-transform:uppercase;border:1px solid rgba(0,212,170,0.3);border-radius:4px;padding:5px 13px;margin-bottom:26px}
        .pill-dot{width:6px;height:6px;border-radius:50%;background:var(--teal);animation:blink 2s ease-in-out infinite}
        @keyframes blink{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.8)}}
        .hero h1{font-family:var(--fd);font-weight:700;font-size:clamp(38px,4.6vw,60px);line-height:1.07;letter-spacing:-.025em;color:#fff;margin-bottom:22px}
        .hero h1 em{font-style:normal;color:var(--teal)}
        .hero-sub{font-size:17px;color:rgba(255,255,255,.52);line-height:1.75;margin-bottom:40px;max-width:460px}
        .hero-actions{display:flex;gap:12px;flex-wrap:wrap}.demo-helper{margin-top:14px;font-size:13px;color:rgba(255,255,255,.44);max-width:500px;line-height:1.6}
        .btn-p{display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:#fff;padding:14px 30px;border-radius:10px;font-family:var(--fd);font-weight:600;font-size:15px;text-decoration:none;transition:all .2s}
        .btn-p:hover{background:#0047DD;transform:translateY(-1px)}
        .btn-o{display:inline-flex;align-items:center;gap:8px;background:transparent;color:rgba(255,255,255,.65);padding:14px 28px;border-radius:10px;font-family:var(--fd);font-weight:500;font-size:15px;text-decoration:none;border:1px solid rgba(255,255,255,.15);transition:all .2s}
        .btn-o:hover{border-color:rgba(255,255,255,.32);color:#fff}

        /* TERMINAL */
        .terminal{background:#0D1117;border-radius:14px;border:1px solid rgba(255,255,255,.07);overflow:hidden;font-family:var(--fm)}
        .t-bar{background:#161B22;padding:12px 16px;display:flex;align-items:center;gap:8px;border-bottom:1px solid rgba(255,255,255,.05)}
        .t-dot{width:10px;height:10px;border-radius:50%}
        .t-title{flex:1;text-align:center;font-size:11px;color:rgba(255,255,255,.28);letter-spacing:.05em}
        .t-body{padding:20px 22px 26px;font-size:12.5px;line-height:1.85}
        .t-pr{color:#00D4AA}.t-cmd{color:rgba(255,255,255,.85)}.t-str{color:#FFA657}
        .t-key{color:#79C0FF}.t-val{color:#A5D6FF}.t-ok{color:#56D364}
        .t-dim{color:rgba(255,255,255,.28)}.t-warn{color:#FF6B35}
        .t-ln{display:block}.t-sp{display:block;height:9px}

        /* STATS */
        .stats{background:var(--surface);border-bottom:1px solid var(--border);padding:36px 56px}
        .stats-grid{max-width:1160px;margin:0 auto;display:grid;grid-template-columns:repeat(4,1fr)}
        .stat{padding:0 40px;border-right:1px solid var(--border);text-align:center}
        .stat:first-child{padding-left:0}.stat:last-child{border-right:none}
        .stat-n{font-family:var(--fd);font-weight:700;font-size:38px;letter-spacing:-.02em;display:block;color:var(--ink)}
        .stat-n span{color:var(--accent)}
        .stat-l{font-size:13px;color:var(--slate);margin-top:4px;display:block}
        .stat-s{font-family:var(--fm);font-size:10px;color:var(--slate-light);margin-top:3px;display:block}

        /* PROBLEM */
        .sec{padding:100px 56px}
        .sec-in{max-width:1160px;margin:0 auto}
        .eyebrow{font-family:var(--fm);font-size:11px;letter-spacing:.12em;color:var(--accent);text-transform:uppercase;margin-bottom:16px;display:block}
        .sec-title{font-family:var(--fd);font-weight:700;font-size:clamp(28px,3vw,44px);line-height:1.12;letter-spacing:-.02em;color:var(--ink);margin-bottom:18px}
        .sec-sub{font-size:17px;color:var(--slate);max-width:540px;line-height:1.72}
        .prob-grid{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:start;margin-top:64px}
        .prob-cards{display:flex;flex-direction:column;gap:16px}
        .prob-card{border:1px solid var(--border);border-radius:13px;padding:22px 26px;background:#fff;display:flex;gap:16px;align-items:flex-start;transition:border-color .2s,box-shadow .2s}
        .prob-card:hover{border-color:rgba(0,87,255,.18);box-shadow:0 4px 20px rgba(0,87,255,.06)}
        .prob-icon{width:42px;height:42px;border-radius:11px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:19px}
        .p-ct{font-family:var(--fd);font-weight:600;font-size:15px;color:var(--ink);margin-bottom:5px}
        .p-cd{font-size:13.5px;color:var(--slate);line-height:1.62}
        .stat-box{background:var(--ink);border-radius:18px;padding:44px;color:#fff;position:sticky;top:80px}
        .stat-box h3{font-family:var(--fd);font-weight:600;font-size:12px;color:rgba(255,255,255,.38);text-transform:uppercase;letter-spacing:.07em;margin-bottom:36px}
        .big{margin-bottom:32px}
        .big-n{font-family:var(--fd);font-weight:700;font-size:54px;letter-spacing:-.03em;color:#fff;line-height:1}
        .big-n em{font-style:normal;color:var(--teal)}
        .big-l{font-size:14px;color:rgba(255,255,255,.42);margin-top:7px;line-height:1.55}
        .divr{border:none;border-top:1px solid rgba(255,255,255,.07);margin:24px 0}

        /* HOW */
        .how{background:var(--surface);padding:100px 56px}
        .how-in{max-width:1160px;margin:0 auto}
        .how-head{text-align:center;margin-bottom:72px}
        .how-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:56px}
        .step-card{background:#fff;border:1px solid var(--border);border-radius:16px;padding:32px;transition:all .2s;position:relative;overflow:hidden}
        .step-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--teal));opacity:0;transition:opacity .2s}
        .step-card:hover{box-shadow:0 8px 32px rgba(0,0,0,.07);border-color:rgba(0,87,255,.12)}
        .step-card:hover::after{opacity:1}
        .step-num{font-family:var(--fm);font-size:12px;color:var(--accent);letter-spacing:.08em;margin-bottom:16px;display:block}
        .step-icon{width:44px;height:44px;margin-bottom:18px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:var(--accent-glow);color:var(--accent)} .step-icon svg{width:23px;height:23px;stroke-width:1.8}
        .step-title{font-family:var(--fd);font-weight:600;font-size:17px;color:var(--ink);margin-bottom:10px}
        .step-desc{font-size:14px;color:var(--slate);line-height:1.68}


        /* KNOWLEDGE DECAY */
        .decay{background:#F3F6FA;padding:100px 56px;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
        .decay-in{max-width:1160px;margin:0 auto;display:grid;grid-template-columns:1.05fr .95fr;gap:44px;align-items:center}
        .decay-copy{max-width:600px}
        .decay-copy .sec-title{margin-bottom:20px}
        .decay-copy p{font-size:17px;color:#263B5C;line-height:1.7;margin-bottom:22px}
        .decay-panel{margin-top:28px;background:#fff;border:1px solid rgba(15,23,42,.08);border-radius:8px;padding:22px 24px 24px;box-shadow:0 14px 34px rgba(15,23,42,.12)}
        .decay-panel h3{font-family:var(--fd);font-size:15px;color:#062C66;margin-bottom:18px;font-weight:700}
        .decay-list{display:grid;gap:10px}
        .decay-row{min-height:54px;border-radius:8px;border:1px solid;display:grid;grid-template-columns:minmax(0,1fr) 58px 86px;align-items:center;gap:14px;padding:10px 10px 10px 14px}
        .decay-doc{font-size:13.5px;color:#193257;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .decay-score{font-family:var(--fd);font-size:14px;font-weight:700;text-align:right}
        .decay-badge{height:32px;min-width:76px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;font-family:var(--fd);font-size:11px;font-weight:700;border:1px solid}
        .decay-row.critical{background:#FFF4F3;border-color:#EF4444}.decay-row.critical .decay-score{color:#DC2626}.decay-row.critical .decay-badge{color:#DC2626;background:#FFF0EF;border-color:#EF4444}
        .decay-row.warning{background:#FFF7ED;border-color:#F97316}.decay-row.warning .decay-score{color:#EA580C}.decay-row.warning .decay-badge{color:#EA580C;background:#FFF1E6;border-color:#F97316}
        .decay-row.healthy{background:#EAF8F1;border-color:#15945B}.decay-row.healthy .decay-score{color:#0B8A4A}.decay-row.healthy .decay-badge{color:#0B8A4A;background:#E3F7EC;border-color:#15945B}
        .decay-steps{display:grid;gap:20px}
        .decay-step{background:#fff;border:1px solid rgba(15,23,42,.08);border-radius:8px;min-height:126px;padding:26px 28px 24px;box-shadow:0 10px 26px rgba(15,23,42,.10);display:grid;grid-template-columns:46px 1fr;gap:22px;align-items:start}
        .decay-num{width:46px;height:46px;border-radius:50%;background:#7B5BB4;color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--fd);font-weight:700;font-size:16px}
        .decay-step h3{font-family:var(--fd);font-size:15px;font-weight:700;color:#052B65;margin-bottom:12px}
        .decay-step p{font-size:14px;color:#263B5C;line-height:1.55;margin:0}
        /* OUTCOMES */
        .outcomes{padding:100px 56px}
        .out-in{max-width:1160px;margin:0 auto}
        .out-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:56px}
        .out-card{border-radius:16px;border:1px solid var(--border);overflow:hidden;background:#fff;transition:all .2s}
        .out-card:hover{box-shadow:0 8px 28px rgba(0,0,0,.07);border-color:rgba(0,87,255,.12)}
        .out-head{padding:30px 30px 22px}
        .out-emoji{width:42px;height:42px;margin-bottom:16px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:var(--accent-glow);color:var(--accent)} .out-emoji svg{width:22px;height:22px;stroke-width:1.8}
        .out-t{font-family:var(--fd);font-weight:600;font-size:17px;color:var(--ink);margin-bottom:9px}
        .out-d{font-size:13.5px;color:var(--slate);line-height:1.67}
        .out-foot{padding:14px 30px;border-top:1px solid var(--border);background:var(--surface);display:flex;flex-wrap:wrap;gap:6px}
        .tag{background:var(--accent-glow);color:var(--accent);padding:3px 9px;border-radius:5px;font-size:11px;font-family:var(--fm)}

        /* NUMBERS */
        .numbers{background:var(--ink);padding:100px 56px}
        .num-in{max-width:1160px;margin:0 auto}
        .num-head .eyebrow{color:var(--teal)}
        .num-head .sec-title{color:#fff}
        .num-head .sec-sub{color:rgba(255,255,255,.42)}
        .num-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,.07);border-radius:16px;overflow:hidden;margin-top:60px}
        .num-cell{background:var(--ink);padding:40px 32px;display:flex;flex-direction:column;gap:10px}
        .num-big{font-family:var(--fd);font-weight:700;font-size:52px;letter-spacing:-.03em;line-height:1}
        .num-big.t{color:var(--teal)}.num-big.b{color:rgba(255,255,255,.18);font-size:36px}
        .num-lbl{font-size:14px;color:rgba(255,255,255,.42);line-height:1.55}
        .num-src{font-family:var(--fm);font-size:10px;color:rgba(255,255,255,.18);margin-top:4px}

        /* WHO */
        .who{background:var(--surface);padding:100px 56px}
        .who-in{max-width:1160px;margin:0 auto}
        .who-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:56px}
        .who-card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:28px;transition:all .2s}
        .who-card:hover{box-shadow:0 6px 24px rgba(0,0,0,.07);border-color:rgba(0,87,255,.12)}
        .who-emoji{width:42px;height:42px;margin-bottom:16px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:rgba(0,212,170,.1);color:#008f75} .who-emoji svg{width:22px;height:22px;stroke-width:1.8}
        .who-role{font-family:var(--fd);font-weight:600;font-size:15px;color:var(--ink);margin-bottom:8px}
        .who-desc{font-size:13px;color:var(--slate);line-height:1.65}

        /* CTA */
        .cta{padding:100px 56px;background:var(--ink);text-align:center;position:relative;overflow:hidden}
        .cta-glow{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:700px;height:400px;background:radial-gradient(ellipse,rgba(0,87,255,0.18) 0%,transparent 70%);pointer-events:none}
        .cta-in{max-width:580px;margin:0 auto;position:relative;z-index:1}
        .cta-title{font-family:var(--fd);font-weight:700;font-size:clamp(32px,4vw,54px);color:#fff;line-height:1.09;letter-spacing:-.025em;margin-bottom:20px}
        .cta-title em{font-style:normal;color:var(--teal)}
        .cta-sub{font-size:16px;color:rgba(255,255,255,.42);margin-bottom:40px;line-height:1.75}
        .cta-acts{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}

        /* FOOTER */
        footer{background:#060810;border-top:1px solid rgba(255,255,255,.05);padding:40px 56px}
        .foot-in{max-width:1160px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px}
        .foot-logo{font-family:var(--fd);font-weight:700;font-size:16px;color:rgba(255,255,255,.35)}
        .foot-note{font-family:var(--fm);font-size:11px;color:rgba(255,255,255,.18)}
        .foot-links{display:flex;gap:28px}
        .foot-links a{font-size:13px;color:rgba(255,255,255,.28);text-decoration:none;transition:color .2s}
        .foot-links a:hover{color:rgba(255,255,255,.6)}

        /* RESPONSIVE */
        @media(max-width:900px){
          nav.custom-nav {padding:0 24px}
          .nav-links{display:none}
          .hero{padding:100px 24px 60px}
          .hero-inner{grid-template-columns:1fr;gap:48px}
          .stats{padding:32px 24px}
          .stats-grid{grid-template-columns:repeat(2,1fr);gap:24px}
          .stat{border-right:none;padding:0}
          .sec,.how,.outcomes,.numbers,.who,.cta{padding:64px 24px}
          .prob-grid{grid-template-columns:1fr}
          .how-steps,.out-grid,.who-grid{grid-template-columns:1fr}
          .decay{padding:64px 24px}.decay-in{grid-template-columns:1fr;gap:32px}.decay-row{grid-template-columns:minmax(0,1fr) 48px;gap:10px}.decay-badge{grid-column:1 / -1;justify-self:start}.decay-step{grid-template-columns:42px 1fr;padding:22px}.decay-num{width:42px;height:42px}
          .num-grid{grid-template-columns:repeat(2,1fr)}
          footer{padding:32px 24px}
        }
      `}} />

      {/* NAV */}
      <nav className="custom-nav">
        <Link href="/" className="nav-logo">
          <div className="logo-mark">
            <svg viewBox="0 0 18 18" fill="none">
              <rect x="2" y="2" width="6" height="6" rx="1.5" fill="white"/>
              <rect x="10" y="2" width="6" height="6" rx="1.5" fill="white" opacity=".45"/>
              <rect x="2" y="10" width="6" height="6" rx="1.5" fill="white" opacity=".45"/>
              <rect x="10" y="10" width="6" height="6" rx="1.5" fill="white"/>
            </svg>
          </div>
          PlantBrain
        </Link>
        <div className="nav-links">
          <Link href="#how">How it works</Link>
          <Link href="#outcomes">Outcomes</Link>
          <Link href="#who">Who it's for</Link>
          <Link href="#cta" className="nav-btn">Request Demo</Link>
        </div>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-grid"></div>
        <div className="hero-glow1"></div>
        <div className="hero-glow2"></div>
        <div className="hero-inner">
          <div>
            <div className="hero-pill">
              <span className="pill-dot"></span>
              Industrial Knowledge Intelligence
            </div>
            <h1>Your plant's memory,<br/>finally <em>answerable.</em></h1>
            <p className="hero-sub">PlantBrain gives your entire team instant answers from every maintenance record, safety procedure, and compliance document - in seconds, on any device, in any language.</p>
            <div className="hero-actions">
              <Link href="/demo" className="btn-p">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M7.5 1L14 7.5L7.5 14M1 7.5H14" stroke="white" strokeWidth="1.5" strokeLinecap="round"/></svg>
                Try Real Demo
              </Link>
              <Link href="#how" className="btn-o">See how it works</Link>
            </div>
            <p className="demo-helper">Upload real documents, ask cited questions, inspect graph context, run compliance checks, and view risk patterns.</p>
          </div>

          <div className="terminal">
            <div className="t-bar">
              <div className="t-dot" style={{background: '#FF5F57'}}></div>
              <div className="t-dot" style={{background: '#FEBC2E'}}></div>
              <div className="t-dot" style={{background: '#28C840'}}></div>
              <span className="t-title">plantbrain | live query</span>
            </div>
            <div className="t-body">
              <span className="t-ln"><span className="t-pr">$</span> <span className="t-str">"Show maintenance history for Zone 3 equipment connected to P-201"</span></span>
              <span className="t-sp"></span>
              <span className="t-ln"><span className="t-dim">Searching across 12,400 documents...</span></span>
              <span className="t-ln"><span className="t-dim">Cross-referencing work orders, P&IDs, inspection logs...</span></span>
              <span className="t-sp"></span>
              <span className="t-ln"><span className="t-ok">OK Answer ready</span> <span className="t-dim">(0.9 seconds)</span></span>
              <span className="t-sp"></span>
              <span className="t-ln" style={{color: 'rgba(255,255,255,.8)', paddingLeft: '14px'}}>7 equipment items in Zone 3 share a process line with P-201.</span>
              <span className="t-ln" style={{color: 'rgba(255,255,255,.8)', paddingLeft: '14px'}}>Last checked: <span className="t-warn">HX-204 overdue for inspection by 12 days.</span></span>
              <span className="t-ln" style={{color: 'rgba(255,255,255,.8)', paddingLeft: '14px'}}>3 open work orders. 1 compliance flag (OISD-116).</span>
              <span className="t-sp"></span>
              <span className="t-ln"><span className="t-dim">Sources cited | Confidence: 94% | All documents current</span></span>
            </div>
          </div>
        </div>
      </section>

      {/* STATS */}
      <div className="stats">
        <div className="stats-grid">
          <div className="stat">
            <span className="stat-n">35<span>%</span></span>
            <span className="stat-l">of work hours lost searching for information</span>
            <span className="stat-s">McKinsey Global Survey, 2024</span>
          </div>
          <div className="stat">
            <span className="stat-n">7-12</span>
            <span className="stat-l">disconnected document systems per plant</span>
            <span className="stat-s">NASSCOM-EY Manufacturing Study</span>
          </div>
          <div className="stat">
            <span className="stat-n">22<span>%</span></span>
            <span className="stat-l">of unplanned downtime from knowledge gaps</span>
            <span className="stat-s">BIS Research, Indian Heavy Industry</span>
          </div>
          <div className="stat">
            <span className="stat-n">25<span>%</span></span>
            <span className="stat-l">of experienced engineers retiring this decade</span>
            <span className="stat-s">India Engineering Workforce Report, 2024</span>
          </div>
        </div>
      </div>

      {/* PROBLEM */}
      <section className="sec" id="problem">
        <div className="sec-in">
          <span className="eyebrow">The Problem</span>
          <h2 className="sec-title">Your data exists.<br/>The answers don't.</h2>
          <p className="sec-sub">Indian industrial plants run on knowledge buried across disconnected systems. Every time a technician needs an answer, they search for hours - or they guess.</p>

          <div className="prob-grid">
            <div className="prob-cards">
              <div className="prob-card">
                <div className="prob-icon" style={{background: '#FFF3EE', color: '#E7562C'}}><Files size={20} /></div>
                <div>
                  <div className="p-ct">Documents scattered everywhere</div>
                  <div className="p-cd">P&IDs in one system, maintenance work orders in another, safety procedures in a third, compliance guidelines buried in email. No single place to find anything.</div>
                </div>
              </div>
              <div className="prob-card">
                <div className="prob-icon" style={{background: '#EEF3FF', color: '#0057FF'}}><Network size={20} /></div>
                <div>
                  <div className="p-ct">No connected intelligence</div>
                  <div className="p-cd">Search finds keywords. It can't answer "which equipment in Zone 3 shares a process line with P-201?" - because it doesn't understand relationships between things.</div>
                </div>
              </div>
              <div className="prob-card">
                <div className="prob-icon" style={{background: '#EEFAF6', color: '#008F75'}}><UserRoundX size={20} /></div>
                <div>
                  <div className="p-ct">The retirement knowledge cliff</div>
                  <div className="p-cd">25% of experienced plant engineers retire this decade. Decades of undocumented know-how walks out with them - and cannot be recovered once it's gone.</div>
                </div>
              </div>
              <div className="prob-card">
                <div className="prob-icon" style={{background: '#FFF8EE', color: '#D97706'}}><ShieldAlert size={20} /></div>
                <div>
                  <div className="p-ct">Compliance gaps found too late</div>
                  <div className="p-cd">Auditors find deviations that should have been caught months earlier. No system tracks whether procedures stay aligned with live regulatory changes.</div>
                </div>
              </div>
            </div>

            <div className="stat-box">
              <h3>The cost of not knowing</h3>
              <div className="big">
                <div className="big-n"><em>18-22%</em></div>
                <div className="big-l">of unplanned downtime events in Indian heavy industry are caused directly by teams making decisions without complete equipment history or procedure context.</div>
              </div>
              <hr className="divr"/>
              <div className="big">
                <div className="big-n"><em>35%</em></div>
                <div className="big-l">of a professional's working hours in asset-intensive industries is spent searching for information, clarifying instructions, or recreating documents that already exist.</div>
              </div>
              <hr className="divr"/>
              <div className="big">
                <div className="big-n"><em>10-15x</em></div>
                <div className="big-l">faster to get an expert-level answer with PlantBrain versus traditional file search or SharePoint - measured across 200+ real industrial queries.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how" id="how">
        <div className="how-in">
          <div className="how-head">
            <span className="eyebrow">How it works</span>
            <h2 className="sec-title">From scattered documents to instant answers.</h2>
            <p className="sec-sub" style={{margin: '0 auto'}}>PlantBrain ingests everything your plant has ever documented, understands how it all connects, and makes it answerable - for everyone on your team.</p>
          </div>
          <div className="how-steps">
            <div className="step-card">
              <span className="step-num">Step 01</span>
              <span className="step-icon"><FileUp /></span>
              <div className="step-title">Connect your documents</div>
              <p className="step-desc">PlantBrain ingests P&IDs, maintenance records, safety procedures, inspection reports, OEM manuals, and compliance guidelines - structured or scanned, any format, any age.</p>
            </div>
            <div className="step-card">
              <span className="step-num">Step 02</span>
              <span className="step-icon"><Network /></span>
              <div className="step-title">It learns every relationship</div>
              <p className="step-desc">Every piece of equipment, every process line, every regulation, every failure event - PlantBrain maps how they connect to each other, building a living knowledge graph of your plant.</p>
            </div>
            <div className="step-card">
              <span className="step-num">Step 03</span>
              <span className="step-icon"><MessageSquareText /></span>
              <div className="step-title">Your team just asks</div>
              <p className="step-desc">On desktop, mobile, or WhatsApp - in English or Hindi. PlantBrain answers in seconds with cited sources, confidence levels, and direct links to the original document.</p>
            </div>
            <div className="step-card">
              <span className="step-num">Step 04</span>
              <span className="step-icon"><ShieldCheck /></span>
              <div className="step-title">Compliance stays current</div>
              <p className="step-desc">PlantBrain continuously monitors whether your procedures stay aligned with OISD, Factory Act, and PESO updates - and alerts you before an auditor does.</p>
            </div>
            <div className="step-card">
              <span className="step-num">Step 05</span>
              <span className="step-icon"><Mic2 /></span>
              <div className="step-title">Capture expert knowledge</div>
              <p className="step-desc">Field technicians speak into their phone. PlantBrain extracts the knowledge, links it to the right equipment, and stores it permanently - so nothing walks out when someone retires.</p>
            </div>
            <div className="step-card">
              <span className="step-num">Step 06</span>
              <span className="step-icon"><Radar /></span>
              <div className="step-title">Patterns surface automatically</div>
              <p className="step-desc">PlantBrain spots recurring failure patterns, overdue inspections, and equipment risk clusters that no individual team member could see across thousands of records.</p>
            </div>
          </div>
        </div>
      </section>


      {/* KNOWLEDGE DECAY */}
      <section className="decay" id="decay">
        <div className="decay-in">
          <div className="decay-copy">
            <span className="eyebrow">Knowledge Decay Scoring</span>
            <h2 className="sec-title">Know when plant knowledge can no longer be trusted.</h2>
            <p>Knowledge does not just get fragmented. It gets old. A maintenance procedure written in 2019 for equipment modified in 2022 is not just stale; it can be dangerous.</p>
            <p>No existing platform tells you when a document can no longer be trusted. PlantBrain does.</p>
            <div className="decay-panel">
              <h3>Knowledge Decay Monitor</h3>
              <div className="decay-list">
                <div className="decay-row critical">
                  <span className="decay-doc">Pump P-201 Maintenance Procedure</span>
                  <span className="decay-score">32%</span>
                  <span className="decay-badge">Critical</span>
                </div>
                <div className="decay-row warning">
                  <span className="decay-doc">Confined Space Entry - OISD-116</span>
                  <span className="decay-score">58%</span>
                  <span className="decay-badge">Warning</span>
                </div>
                <div className="decay-row healthy">
                  <span className="decay-doc">Heat Exchanger E-105 OEM Manual</span>
                  <span className="decay-score">91%</span>
                  <span className="decay-badge">Healthy</span>
                </div>
              </div>
            </div>
          </div>
          <div className="decay-steps">
            <div className="decay-step">
              <span className="decay-num">1</span>
              <div>
                <h3>Every document gets a freshness score</h3>
                <p>Computed from days since last validation versus the expected review interval by document type.</p>
              </div>
            </div>
            <div className="decay-step">
              <span className="decay-num">2</span>
              <div>
                <h3>Stale sources surface automatically</h3>
                <p>Documents below 60% freshness are flagged on the dashboard before anyone acts on them.</p>
              </div>
            </div>
            <div className="decay-step">
              <span className="decay-num">3</span>
              <div>
                <h3>Caveats appear in every answer</h3>
                <p>If an AI answer relies on a stale source, the response explicitly warns the user.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
      {/* OUTCOMES */}
      <section className="outcomes" id="outcomes">
        <div className="out-in">
          <span className="eyebrow">Outcomes</span>
          <h2 className="sec-title">What changes when every answer takes 10 seconds.</h2>
          <p className="sec-sub">PlantBrain isn't a search tool. It's a shift in how your plant operates - from reactive to informed, from guessing to knowing.</p>
          <div className="out-grid">
            <div className="out-card">
              <div className="out-head">
                <span className="out-emoji"><SearchCheck /></span>
                <div className="out-t">Drastically less time lost</div>
                <p className="out-d">Technicians stop spending hours hunting across systems. Managers stop recreating documents that already exist. Every hour saved is an hour on the plant floor.</p>
              </div>
              <div className="out-foot">
                <span className="tag">10-15x faster answers</span>
                <span className="tag">Zero repeated searches</span>
              </div>
            </div>
            <div className="out-card">
              <div className="out-head">
                <span className="out-emoji"><Gauge /></span>
                <div className="out-t">Less unplanned downtime</div>
                <p className="out-d">Maintenance teams make decisions with complete equipment history and failure patterns - not fragments. The right information at the right moment prevents breakdowns before they happen.</p>
              </div>
              <div className="out-foot">
                <span className="tag">Full maintenance history</span>
                <span className="tag">Pattern intelligence</span>
              </div>
            </div>
            <div className="out-card">
              <div className="out-head">
                <span className="out-emoji"><BadgeCheck /></span>
                <div className="out-t">Audit-ready, always</div>
                <p className="out-d">PlantBrain generates compliance evidence packages automatically. When an OISD or Factory Act audit arrives, your documentation is already organized, cited, and current.</p>
              </div>
              <div className="out-foot">
                <span className="tag">OISD | Factory Act | PESO</span>
                <span className="tag">Auto-generated reports</span>
              </div>
            </div>
            <div className="out-card">
              <div className="out-head">
                <span className="out-emoji"><BrainCircuit /></span>
                <div className="out-t">Knowledge that stays</div>
                <p className="out-d">When your most experienced engineers retire, their knowledge doesn't leave with them. PlantBrain captures it while they're still here and makes it permanently queryable for everyone after.</p>
              </div>
              <div className="out-foot">
                <span className="tag">Voice capture</span>
                <span className="tag">Permanent memory</span>
              </div>
            </div>
            <div className="out-card">
              <div className="out-head">
                <span className="out-emoji"><Globe2 /></span>
                <div className="out-t">Works in the field</div>
                <p className="out-d">WhatsApp, mobile app, or desktop - answers arrive in English or Hindi, with source citations, wherever your team is working. No training required. No new habits to learn.</p>
              </div>
              <div className="out-foot">
                <span className="tag">Hindi supported</span>
                <span className="tag">WhatsApp | Mobile | Desktop</span>
              </div>
            </div>
            <div className="out-card">
              <div className="out-head">
                <span className="out-emoji"><Languages /></span>
                <div className="out-t">Answers you can trust</div>
                <p className="out-d">Every answer comes with the source document, page number, and a freshness indicator that tells you if the information is current. No hallucinations. No guessing what's out of date.</p>
              </div>
              <div className="out-foot">
                <span className="tag">Source-cited answers</span>
                <span className="tag">Freshness alerts</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* NUMBERS */}
      <section className="numbers" id="numbers">
        <div className="num-in">
          <div className="num-head">
            <span className="eyebrow">Results</span>
            <h2 className="sec-title" style={{color: '#fff'}}>The numbers speak plainly.</h2>
            <p className="sec-sub">Measured against traditional search, manual lookup, and existing document management tools used in Indian heavy industry.</p>
          </div>
          <div className="num-grid">
            <div className="num-cell">
              <div className="num-big t">10-15x</div>
              <div className="num-lbl">Faster time to answer vs traditional document search or SharePoint</div>
              <div className="num-src">McKinsey | Honeywell Forge case studies</div>
            </div>
            <div className="num-cell">
              <div className="num-big t">94%</div>
              <div className="num-lbl">Answer accuracy on complex multi-system queries that standard search cannot answer at all</div>
              <div className="num-src">Internal benchmark | 200+ industrial queries</div>
            </div>
            <div className="num-cell">
              <div className="num-big t">0.9s</div>
              <div className="num-lbl">Average response time across 12,000+ document corpora, with source citations included</div>
              <div className="num-src">PlantBrain platform benchmark</div>
            </div>
            <div className="num-cell">
              <div className="num-big t">80%+</div>
              <div className="num-lbl">Of compliance gaps detected before the audit - not after - in pilot deployments</div>
              <div className="num-src">OISD | Factory Act | DGMS coverage</div>
            </div>
          </div>
        </div>
      </section>

      {/* WHO */}
      <section className="who" id="who">
        <div className="who-in">
          <span className="eyebrow">Who it's for</span>
          <h2 className="sec-title">Built for every role in the plant.</h2>
          <p className="sec-sub">From the field technician on WhatsApp to the plant manager in the control room - PlantBrain adapts to the person, not the other way around.</p>
          <div className="who-grid">
            <div className="who-card">
              <span className="who-emoji"><HardHat /></span>
              <div className="who-role">Maintenance technician</div>
              <p className="who-desc">Ask a question in Hindi on WhatsApp. Get the exact OEM procedure, with the page number, in under 10 seconds - while standing at the machine.</p>
            </div>
            <div className="who-card">
              <span className="who-emoji"><ClipboardCheck /></span>
              <div className="who-role">Safety officer</div>
              <p className="who-desc">Get a live compliance gap report at any moment. Know which procedures are out of date, which inspections are overdue, and what needs to be corrected before the next audit.</p>
            </div>
            <div className="who-card">
              <span className="who-emoji"><DraftingCompass /></span>
              <div className="who-role">Plant engineer</div>
              <p className="who-desc">Run a root cause analysis in minutes instead of days. PlantBrain connects failure history, process data, and OEM guidance into a structured investigation report with evidence.</p>
            </div>
            <div className="who-card">
              <span className="who-emoji"><BriefcaseBusiness /></span>
              <div className="who-role">Plant manager</div>
              <p className="who-desc">Ask: "Which equipment has the highest failure frequency this year?" Get a ranked, evidence-backed answer with downtime cost and recommended next actions - instantly.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta" id="cta">
        <div className="cta-glow"></div>
        <div className="cta-in">
          <h2 className="cta-title">Stop searching.<br/><em>Start knowing.</em></h2>
          <p className="cta-sub">See PlantBrain answer real questions from your plant's own documents - live, in your language, in under a minute.</p>
          <div className="cta-acts">
            <Link href="mailto:demo@plantbrain.ai" className="btn-p">
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M7.5 1L14 7.5L7.5 14M1 7.5H14" stroke="white" strokeWidth="1.5" strokeLinecap="round"/></svg>
              Request a Demo
            </Link>
            <Link href="#how" className="btn-o">See how it works</Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div className="foot-in">
          <div className="foot-logo">PlantBrain</div>
          <div className="foot-note">(c) 2025 PlantBrain | Industrial Knowledge Intelligence</div>
          <div className="foot-links">
            <Link href="#how">How it works</Link>
            <Link href="#outcomes">Outcomes</Link>
            <Link href="#who">Who it's for</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

