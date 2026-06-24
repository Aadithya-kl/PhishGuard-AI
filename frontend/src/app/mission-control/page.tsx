"use client";

import React, { useState, useEffect } from "react";
import { IntelCard } from "@/components/ui/intel-card";
import { MetricDisplay } from "@/components/ui/metric-display";
import { SecurityScore } from "@/components/dashboard/security-score";
import { ThreatTimeline } from "@/components/dashboard/threat-timeline";
import { MitreHeatmap } from "@/components/dashboard/mitre-heatmap";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { AlertTriangle, ShieldAlert, Crosshair, Network, BarChart2 } from "lucide-react";
import { api } from "@/lib/api";

// Mock Data
const timelineData = Array.from({ length: 24 }).map((_, i) => ({
  timestamp: Date.now() - (23 - i) * 3600000,
  threats: Math.floor(Math.random() * 50) + 10,
  safe: Math.floor(Math.random() * 200) + 100,
}));

const mitreData = [
  {
    id: "TA0001", name: "Initial Access", techniques: [
      { id: "T1566", name: "Phishing", coverage: 95, detections: 142 },
      { id: "T1190", name: "Exploit Public-Facing App", coverage: 40, detections: 12 },
      { id: "T1133", name: "External Remote Services", coverage: 60, detections: 5 },
    ]
  },
  {
    id: "TA0002", name: "Execution", techniques: [
      { id: "T1059", name: "Command and Scripting Interpreter", coverage: 85, detections: 89 },
      { id: "T1204", name: "User Execution", coverage: 70, detections: 45 },
      { id: "T1053", name: "Scheduled Task/Job", coverage: 50, detections: 8 },
    ]
  },
  {
    id: "TA0005", name: "Defense Evasion", techniques: [
      { id: "T1140", name: "Deobfuscate/Decode Files or Information", coverage: 75, detections: 34 },
      { id: "T1070", name: "Indicator Removal", coverage: 65, detections: 19 },
      { id: "T1218", name: "System Binary Proxy Execution", coverage: 55, detections: 7 },
    ]
  },
  {
    id: "TA0006", name: "Credential Access", techniques: [
      { id: "T1003", name: "OS Credential Dumping", coverage: 90, detections: 56 },
      { id: "T1110", name: "Brute Force", coverage: 80, detections: 210 },
      { id: "T1555", name: "Credentials from Passwords Stores", coverage: 75, detections: 43 },
    ]
  },
];

const activityData: any[] = [
  { id: "1", type: "detection", severity: "critical", title: "Phishing Campaign Detected", description: "Large scale credential harvesting targeting HR department.", timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString() },
  { id: "2", type: "investigation", severity: "high", title: "Investigation Auto-Opened", description: "AI Agent initiated investigation into suspicious login from unusual IP.", timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
  { id: "3", type: "response", severity: "medium", title: "Automated Block Applied", description: "Domain evil-corp.xyz blocked across tenant by Policy Guard.", timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString() },
  { id: "4", type: "intel", severity: "info", title: "Threat Intel Sync", description: "Ingested 1,204 new IOCs from CrowdStrike feed.", timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString() },
];

export default function MissionControlPage() {
  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto p-2 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline">Mission Control</h1>
          <p className="text-sm text-slate-500 mt-1">Global security posture and active threats</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-fast shadow-[0_0_15px_rgba(99,102,241,0.3)] border border-indigo-400/30">
            Generate Briefing
          </button>
        </div>
      </div>

      {/* Top Row: Metrics & Posture */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <IntelCard className="col-span-1 md:col-span-1 flex items-center justify-center p-6" accentColor="indigo" accentPosition="top">
          <SecurityScore score={82} size={160} trend="up" />
        </IntelCard>

        <div className="col-span-1 md:col-span-3 grid grid-cols-3 gap-6">
          <IntelCard className="p-6 flex flex-col justify-between" interactive>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <span className="text-[10px] font-mono text-red-400 bg-red-500/10 px-2 py-1 rounded">CRITICAL</span>
            </div>
            <MetricDisplay 
              label="Active Threats" 
              value={24} 
              trend={{ direction: "down", value: "-12%" }} 
              trendSentiment="positive"
            />
          </IntelCard>

          <IntelCard className="p-6 flex flex-col justify-between" interactive>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                <Crosshair className="w-5 h-5 text-indigo-400" />
              </div>
              <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded">OPEN</span>
            </div>
            <MetricDisplay 
              label="Active Investigations" 
              value={12} 
              trend={{ direction: "up", value: "+3" }} 
              trendSentiment="negative"
            />
          </IntelCard>

          <IntelCard className="p-6 flex flex-col justify-between" interactive>
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                <Network className="w-5 h-5 text-cyan-400" />
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded">TRACKING</span>
            </div>
            <MetricDisplay 
              label="Known Campaigns" 
              value={8} 
              trend={{ direction: "flat", value: "0" }} 
              trendSentiment="neutral"
            />
          </IntelCard>
        </div>
      </div>

      {/* Middle Row: Timeline & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[400px]">
        <IntelCard className="col-span-2 p-6 flex flex-col" accentColor="none">
          <div className="flex items-center justify-between mb-6 shrink-0">
            <h3 className="text-title">Threat Velocity</h3>
            <div className="flex gap-2">
              <button className="px-2 py-1 text-xs font-medium bg-white/[0.05] rounded text-slate-300">24h</button>
              <button className="px-2 py-1 text-xs font-medium text-slate-500 hover:text-slate-300">7d</button>
              <button className="px-2 py-1 text-xs font-medium text-slate-500 hover:text-slate-300">30d</button>
            </div>
          </div>
          <div className="flex-1 min-h-0">
            <ThreatTimeline data={timelineData} />
          </div>
        </IntelCard>

        <IntelCard className="col-span-1 p-6 flex flex-col" accentColor="none">
          <div className="flex items-center justify-between mb-6 shrink-0">
            <h3 className="text-title">Live Intel Feed</h3>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
          </div>
          <div className="flex-1 overflow-y-auto pr-2">
            <ActivityFeed events={activityData} />
          </div>
        </IntelCard>
      </div>

      {/* Bottom Row: MITRE */}
      <IntelCard className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-title">MITRE ATT&CK Coverage Matrix</h3>
          <button className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            <BarChart2 className="w-3 h-3" /> View Full Matrix
          </button>
        </div>
        <MitreHeatmap tactics={mitreData} />
      </IntelCard>
    </div>
  );
}
