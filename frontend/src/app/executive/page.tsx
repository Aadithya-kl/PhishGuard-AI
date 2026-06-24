"use client";

import { useState, useEffect } from "react";
import { IntelCard } from "@/components/ui/intel-card";
import { MetricDisplay } from "@/components/ui/metric-display";
import { Shield, TrendingUp, Activity, Crosshair, Bot, AlertTriangle, ArrowUpRight } from "lucide-react";
import { StatusIndicator } from "@/components/ui/status-indicator";

export default function ExecutiveDashboard() {
  const [data, setData] = useState<any>(null);
  
  useEffect(() => {
    // Simulating Phase 9.6 executive payload
    setTimeout(() => {
      setData({
        posture: { score: 82, rating: "Good" },
        overview: {
          total_scans: 125430,
          threats_detected: 432,
          active_investigations: 12,
          mttd_minutes: 2.4,
          mttr_minutes: 45.0
        },
        automation: {
          acceptance_rate: 85.5,
          false_action_rate: 1.2,
          trust_score: 91.0
        },
        copilot: {
          operational: { total_queries: 1542, avg_confidence: 94.2 },
          evaluation: { citation_rate: 98.1, hallucination_rate: 0.5 }
        },
        readiness: {
          status: "READY_FOR_ACTIVE_RESPONSE"
        }
      });
    }, 500);
  }, []);

  if (!data) return (
    <div className="flex h-[calc(100vh-56px)] items-center justify-center bg-[#020617]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 rounded-full border-t-2 border-r-2 border-indigo-500 animate-spin" />
        <p className="text-xs font-mono text-slate-500 uppercase tracking-widest">Aggregating Telemetry...</p>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto p-2 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline">Executive Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">Strategic Security Posture & Automation Readiness</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-fast shadow-[0_0_15px_rgba(99,102,241,0.3)] border border-indigo-400/30">
            Export Board Report
          </button>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <IntelCard className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">Global Risk Score</h3>
            <div className="w-8 h-8 rounded bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Shield className="w-4 h-4 text-emerald-400" />
            </div>
          </div>
          <div className="text-display text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.5)]">
            {data.posture.score}
          </div>
          <div className="mt-2 text-xs text-slate-400">Target {">"} 80</div>
        </IntelCard>

        <IntelCard className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">MTTD</h3>
            <div className="w-8 h-8 rounded bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Activity className="w-4 h-4 text-indigo-400" />
            </div>
          </div>
          <div className="text-4xl font-light tabular-nums text-slate-200">
            {data.overview.mttd_minutes}<span className="text-lg text-slate-500 ml-1">min</span>
          </div>
          <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1">
            <ArrowUpRight className="w-3 h-3 rotate-180" /> -12% vs last month
          </div>
        </IntelCard>

        <IntelCard className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">MTTR</h3>
            <div className="w-8 h-8 rounded bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
              <Crosshair className="w-4 h-4 text-orange-400" />
            </div>
          </div>
          <div className="text-4xl font-light tabular-nums text-slate-200">
            {data.overview.mttr_minutes}<span className="text-lg text-slate-500 ml-1">min</span>
          </div>
          <div className="mt-2 text-xs text-emerald-400 flex items-center gap-1">
            <ArrowUpRight className="w-3 h-3 rotate-180" /> -4% vs last month
          </div>
        </IntelCard>

        <IntelCard className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">Automation Trust</h3>
            <div className="w-8 h-8 rounded bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
              <Bot className="w-4 h-4 text-cyan-400" />
            </div>
          </div>
          <div className="text-display text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]">
            {data.automation.trust_score}
          </div>
          <div className="mt-2 text-xs text-slate-400">Target {">"} 85 for Active Response</div>
        </IntelCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Automation Governance */}
        <IntelCard className="p-6" accentColor="indigo">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-title">Automation Readiness</h3>
            <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded border border-emerald-500/20">
              {data.readiness.status}
            </span>
          </div>
          <div className="space-y-4">
            <div className="surface-0 rounded-xl p-4 border border-white/[0.04]">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold text-slate-300">Analyst Acceptance Rate</span>
                <span className="text-sm font-mono text-cyan-400">{data.automation.acceptance_rate}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-cyan-400 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.5)]" style={{ width: `${data.automation.acceptance_rate}%` }} />
              </div>
            </div>
            
            <div className="surface-0 rounded-xl p-4 border border-white/[0.04]">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold text-slate-300">False Action Rate</span>
                <span className="text-sm font-mono text-emerald-400">{data.automation.false_action_rate}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-400 rounded-full shadow-[0_0_10px_rgba(52,211,153,0.5)]" style={{ width: `${Math.max(2, data.automation.false_action_rate * 5)}%` }} />
              </div>
              <div className="mt-2 text-[10px] text-slate-500">Must remain &lt; 2.0%</div>
            </div>
          </div>
        </IntelCard>

        {/* Copilot Evaluation */}
        <IntelCard className="p-6" accentColor="indigo">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-title">Copilot Fleet Telemetry</h3>
            <span className="text-[10px] text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
              <StatusIndicator level="safe" size="sm" pulse /> Health Nominal
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="surface-0 rounded-xl p-4 border border-white/[0.04]">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Total Queries</div>
              <div className="text-2xl font-light font-mono text-slate-200">{data.copilot.operational.total_queries}</div>
            </div>
            <div className="surface-0 rounded-xl p-4 border border-white/[0.04]">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Avg Confidence</div>
              <div className="text-2xl font-light font-mono text-indigo-400">{data.copilot.operational.avg_confidence}%</div>
            </div>
            <div className="surface-0 rounded-xl p-4 border border-white/[0.04]">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Citation Rate</div>
              <div className="text-2xl font-light font-mono text-slate-200">{data.copilot.evaluation.citation_rate}%</div>
            </div>
            <div className="surface-0 rounded-xl p-4 border border-white/[0.04]">
              <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">Hallucinations</div>
              <div className="text-2xl font-light font-mono text-emerald-400">{data.copilot.evaluation.hallucination_rate}%</div>
            </div>
          </div>
        </IntelCard>
      </div>
    </div>
  );
}
