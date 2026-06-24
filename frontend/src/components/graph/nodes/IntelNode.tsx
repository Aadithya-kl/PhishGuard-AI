import React, { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { ShieldAlert, Crosshair, Server, Target, FileSearch, Zap, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

export type NodeType = "actor" | "campaign" | "infrastructure" | "ioc" | "victim" | "investigation" | "response";

export interface IntelNodeData {
  id: string;
  type: NodeType;
  label: string;
  subtitle?: string;
  risk_score?: number;
  status?: string;
  isExpanded?: boolean;
}

const config = {
  actor: {
    icon: ShieldAlert,
    colors: "bg-red-500/10 border-red-500/30 text-red-400",
    glow: "shadow-[0_0_20px_rgba(239,68,68,0.15)]",
    bgAccent: "from-red-500/20 to-transparent",
  },
  campaign: {
    icon: Crosshair,
    colors: "bg-orange-500/10 border-orange-500/30 text-orange-400",
    glow: "shadow-[0_0_20px_rgba(249,115,22,0.15)]",
    bgAccent: "from-orange-500/20 to-transparent",
  },
  infrastructure: {
    icon: Server,
    colors: "bg-slate-500/10 border-slate-500/30 text-slate-400",
    glow: "shadow-[0_0_15px_rgba(148,163,184,0.1)]",
    bgAccent: "from-slate-500/20 to-transparent",
  },
  ioc: {
    icon: Activity,
    colors: "bg-indigo-500/10 border-indigo-500/30 text-indigo-400",
    glow: "shadow-[0_0_15px_rgba(99,102,241,0.15)]",
    bgAccent: "from-indigo-500/20 to-transparent",
  },
  victim: {
    icon: Target,
    colors: "bg-amber-500/10 border-amber-500/30 text-amber-400",
    glow: "shadow-[0_0_15px_rgba(245,158,11,0.15)]",
    bgAccent: "from-amber-500/20 to-transparent",
  },
  investigation: {
    icon: FileSearch,
    colors: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
    glow: "shadow-[0_0_15px_rgba(6,182,212,0.15)]",
    bgAccent: "from-cyan-500/20 to-transparent",
  },
  response: {
    icon: Zap,
    colors: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
    glow: "shadow-[0_0_15px_rgba(16,185,129,0.15)]",
    bgAccent: "from-emerald-500/20 to-transparent",
  },
};

export const IntelNode = memo(({ data, selected }: { data: IntelNodeData; selected: boolean }) => {
  const nodeConfig = config[data.type];
  const Icon = nodeConfig.icon;

  return (
    <div
      className={cn(
        "relative flex flex-col min-w-[200px] surface-1 rounded-xl border border-white/[0.08] transition-all duration-300 overflow-hidden",
        selected ? "ring-2 ring-indigo-500 ring-offset-2 ring-offset-[#0f172a] shadow-[0_0_30px_rgba(99,102,241,0.3)] scale-105 z-50" : "hover:border-white/[0.15] hover:scale-[1.02]",
        nodeConfig.glow
      )}
    >
      {/* Background Accent */}
      <div className={cn("absolute top-0 left-0 right-0 h-12 bg-gradient-to-b opacity-50 pointer-events-none", nodeConfig.bgAccent)} />

      {/* Handles */}
      <Handle type="target" position={Position.Top} className="w-2 h-2 rounded-sm border-0 bg-slate-400" />
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 rounded-sm border-0 bg-slate-400" />

      {/* Header */}
      <div className="flex items-start justify-between p-3 shrink-0 relative z-10">
        <div className={cn("p-1.5 rounded-lg border", nodeConfig.colors, "bg-background")}>
          <Icon className="w-4 h-4" />
        </div>
        {data.risk_score !== undefined && (
          <div className={cn(
            "text-[10px] font-mono px-1.5 py-0.5 rounded border font-bold",
            data.risk_score >= 90 ? "bg-red-500/20 text-red-400 border-red-500/30" :
            data.risk_score >= 70 ? "bg-orange-500/20 text-orange-400 border-orange-500/30" :
            "bg-indigo-500/20 text-indigo-400 border-indigo-500/30"
          )}>
            {data.risk_score}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="px-3 pb-3 relative z-10 flex flex-col gap-0.5">
        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">{data.type}</span>
        <span className="text-sm font-medium text-slate-200 truncate">{data.label}</span>
        {data.subtitle && (
          <span className="text-xs text-slate-400 truncate mt-1">{data.subtitle}</span>
        )}
      </div>
    </div>
  );
});

IntelNode.displayName = "IntelNode";
