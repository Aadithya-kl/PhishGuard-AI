"use client";

import { useState } from "react";
import { IntelCard } from "@/components/ui/intel-card";
import { MetricDisplay } from "@/components/ui/metric-display";
import { Zap, ShieldAlert, CheckCircle2, XCircle, Clock, AlertTriangle } from "lucide-react";
import { StatusIndicator } from "@/components/ui/status-indicator";

const pendingActions = [
  { id: "ACT-001", type: "Block Domain", target: "evil-corp.xyz", risk: "HIGH", time: "2m ago", status: "pending" },
  { id: "ACT-002", type: "Isolate Host", target: "DESKTOP-9X42", risk: "CRITICAL", time: "5m ago", status: "pending" },
  { id: "ACT-003", type: "Disable User", target: "j.smith@corp.com", risk: "MEDIUM", time: "12m ago", status: "pending" },
];

const recentActions = [
  { id: "ACT-004", type: "Delete Email", target: "msg_12345", status: "success", time: "1h ago", mode: "Auto" },
  { id: "ACT-005", type: "Block IP", target: "185.122.204.3", status: "success", time: "2h ago", mode: "Manual" },
  { id: "ACT-006", type: "Reset Password", target: "m.jones@corp.com", status: "failed", time: "3h ago", mode: "Auto" },
];

export default function ResponseDashboard() {
  const [globalState, setGlobalState] = useState("OBSERVATION");

  return (
    <div className="flex flex-col gap-6 max-w-[1600px] mx-auto p-2 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline">Active Response</h1>
          <p className="text-sm text-slate-500 mt-1">Autonomous Execution & Governance Center</p>
        </div>
        <div className="flex items-center gap-4 liquid-glass px-4 py-2 rounded-xl border border-white/10">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Global State</span>
          <div className="h-4 w-px bg-white/10" />
          <select 
            value={globalState}
            onChange={(e) => setGlobalState(e.target.value)}
            className={`bg-transparent outline-none text-xs font-semibold cursor-pointer ${
              globalState === "DISABLED" ? "text-red-400" :
              globalState === "OBSERVATION" ? "text-amber-400" :
              "text-emerald-400"
            }`}
          >
            <option value="DISABLED" className="bg-slate-900 text-red-400">DISABLED (Kill Switch)</option>
            <option value="OBSERVATION" className="bg-slate-900 text-amber-400">OBSERVATION ONLY</option>
            <option value="LIMITED_ACTIVE" className="bg-slate-900 text-emerald-400">LIMITED ACTIVE</option>
            <option value="FULL_ACTIVE" className="bg-slate-900 text-emerald-400">FULL ACTIVE</option>
          </select>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <IntelCard className="p-6">
          <MetricDisplay 
            label="Pending Approvals" 
            value={12} 
            trend={{ direction: "up", value: "+4" }} 
            trendSentiment="negative"
          />
        </IntelCard>
        <IntelCard className="p-6">
          <MetricDisplay 
            label="Actions Executed (24h)" 
            value={845} 
            trend={{ direction: "up", value: "+12%" }} 
            trendSentiment="neutral"
          />
        </IntelCard>
        <IntelCard className="p-6">
          <MetricDisplay 
            label="False Action Rate" 
            value={1.2} 

            trend={{ direction: "down", value: "-0.3%" }} 
            trendSentiment="positive"
          />
        </IntelCard>
        <IntelCard className="p-6">
          <MetricDisplay 
            label="Automation Trust" 
            value={94} 
            trend={{ direction: "flat", value: "0" }} 
            trendSentiment="positive"
          />
        </IntelCard>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[500px]">
        {/* Pending Actions */}
        <IntelCard className="flex flex-col p-6" accentColor="amber">
          <div className="flex items-center justify-between mb-6 shrink-0">
            <h3 className="text-title flex items-center gap-2">
              <Clock className="w-4 h-4 text-orange-400" />
              Pending Human Approval
            </h3>
            <span className="text-[10px] font-mono bg-orange-500/10 text-orange-400 px-2 py-1 rounded border border-orange-500/20">
              ACTION REQUIRED
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-3">
            {pendingActions.map(action => (
              <div key={action.id} className="surface-0 border border-white/[0.04] p-4 rounded-xl hover:border-white/10 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="text-[10px] text-slate-500 font-mono mb-1">{action.id}</div>
                    <div className="text-sm font-semibold text-slate-200">{action.type}</div>
                  </div>
                  <div className="text-[10px] text-slate-400">{action.time}</div>
                </div>
                
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-[10px] text-slate-500 uppercase">Target:</span>
                  <span className="text-xs font-mono text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded">{action.target}</span>
                </div>

                <div className="flex gap-2">
                  <button className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg py-2 text-xs font-semibold transition-colors flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                  </button>
                  <button className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg py-2 text-xs font-semibold transition-colors flex items-center justify-center gap-2">
                    <XCircle className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </IntelCard>

        {/* Action Log */}
        <IntelCard className="flex flex-col p-6" accentColor="indigo">
          <div className="flex items-center justify-between mb-6 shrink-0">
            <h3 className="text-title flex items-center gap-2">
              <Zap className="w-4 h-4 text-indigo-400" />
              Action Execution Log
            </h3>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.04] text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  <th className="pb-3 font-medium">Action</th>
                  <th className="pb-3 font-medium">Target</th>
                  <th className="pb-3 font-medium">Mode</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium text-right">Time</th>
                </tr>
              </thead>
              <tbody className="text-xs text-slate-300">
                {recentActions.map((action, i) => (
                  <tr key={i} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 font-medium text-slate-200">{action.type}</td>
                    <td className="py-3 font-mono text-[10px] text-indigo-300">{action.target}</td>
                    <td className="py-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${action.mode === "Auto" ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" : "bg-slate-500/10 text-slate-400 border border-slate-500/20"}`}>
                        {action.mode}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex items-center gap-1.5">
                        {action.status === "success" ? (
                          <StatusIndicator level="safe" size="sm" />
                        ) : (
                          <StatusIndicator level="critical" size="sm" />
                        )}
                        <span className="capitalize">{action.status}</span>
                      </div>
                    </td>
                    <td className="py-3 text-right text-slate-500">{action.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </IntelCard>
      </div>
    </div>
  );
}
