"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, ShieldAlert, Crosshair, Server, Activity, Target, FileSearch, Zap, ArrowUpRight, BarChart2, Shield } from "lucide-react";
import { IntelNodeData } from "./nodes/IntelNode";
import { cn } from "@/lib/utils";

interface GraphSidebarProps {
  selectedNode: IntelNodeData | null;
  onClose: () => void;
}

export function GraphSidebar({ selectedNode, onClose }: GraphSidebarProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case "actor": return ShieldAlert;
      case "campaign": return Crosshair;
      case "infrastructure": return Server;
      case "ioc": return Activity;
      case "victim": return Target;
      case "investigation": return FileSearch;
      case "response": return Zap;
      default: return Shield;
    }
  };

  const getColors = (type: string) => {
    switch (type) {
      case "actor": return "text-red-400 bg-red-500/10 border-red-500/30";
      case "campaign": return "text-orange-400 bg-orange-500/10 border-orange-500/30";
      case "infrastructure": return "text-slate-400 bg-slate-500/10 border-slate-500/30";
      case "ioc": return "text-indigo-400 bg-indigo-500/10 border-indigo-500/30";
      case "victim": return "text-amber-400 bg-amber-500/10 border-amber-500/30";
      case "investigation": return "text-cyan-400 bg-cyan-500/10 border-cyan-500/30";
      case "response": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
      default: return "text-slate-400 bg-slate-500/10 border-slate-500/30";
    }
  };

  return (
    <AnimatePresence>
      {selectedNode && (
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="absolute top-6 right-6 bottom-6 w-96 liquid-glass-elevated rounded-2xl flex flex-col z-50 overflow-hidden shadow-2xl border border-white/10"
        >
          {/* Header */}
          <div className="p-5 border-b border-white/[0.08] flex items-start justify-between shrink-0 bg-white/[0.02]">
            <div className="flex gap-3 items-start">
              {(() => {
                const Icon = getIcon(selectedNode.type);
                const colors = getColors(selectedNode.type);
                return (
                  <div className={cn("p-2 rounded-lg border", colors)}>
                    <Icon className="w-5 h-5" />
                  </div>
                );
              })()}
              <div>
                <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-1">
                  {selectedNode.type}
                </div>
                <h3 className="text-sm font-semibold text-slate-200 leading-tight">
                  {selectedNode.label}
                </h3>
                {selectedNode.subtitle && (
                  <p className="text-xs text-slate-400 mt-0.5">{selectedNode.subtitle}</p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-white/10 text-slate-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-6">
            {/* Intel Context */}
            <div>
              <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3">
                Intelligence Context
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="surface-0 rounded-lg p-3 border border-white/[0.04]">
                  <div className="text-[10px] text-slate-500 uppercase mb-1">Risk Score</div>
                  <div className={cn(
                    "text-xl font-bold font-mono",
                    (selectedNode.risk_score || 0) >= 90 ? "text-red-400 drop-shadow-[0_0_8px_rgba(248,113,113,0.5)]" :
                    (selectedNode.risk_score || 0) >= 70 ? "text-orange-400 drop-shadow-[0_0_8px_rgba(251,146,60,0.5)]" :
                    "text-indigo-400 drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]"
                  )}>
                    {selectedNode.risk_score || "N/A"}
                  </div>
                </div>
                <div className="surface-0 rounded-lg p-3 border border-white/[0.04]">
                  <div className="text-[10px] text-slate-500 uppercase mb-1">First Seen</div>
                  <div className="text-sm font-medium text-slate-300">2d ago</div>
                </div>
              </div>
            </div>

            {/* MITRE Mapping */}
            {(selectedNode.type === "actor" || selectedNode.type === "campaign" || selectedNode.type === "ioc") && (
              <div>
                <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3 flex items-center justify-between">
                  MITRE Mapping
                  <BarChart2 className="w-3 h-3 text-indigo-400" />
                </h4>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between px-3 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-md">
                    <span className="text-xs font-medium text-indigo-300">T1566 - Phishing</span>
                    <span className="text-[10px] bg-indigo-500/20 text-indigo-200 px-1.5 py-0.5 rounded">High Confidence</span>
                  </div>
                  <div className="flex items-center justify-between px-3 py-2 bg-slate-800/50 border border-white/[0.04] rounded-md">
                    <span className="text-xs font-medium text-slate-300">T1204 - User Execution</span>
                    <span className="text-[10px] bg-white/[0.05] text-slate-400 px-1.5 py-0.5 rounded">Observed</span>
                  </div>
                </div>
              </div>
            )}

            {/* Recommended Actions */}
            <div>
              <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3">
                Recommended Actions
              </h4>
              <div className="flex flex-col gap-2">
                <button className="flex items-center justify-between px-3 py-2.5 surface-1 hover:bg-indigo-500/10 border border-white/[0.06] hover:border-indigo-500/30 rounded-lg transition-fast group text-left">
                  <div>
                    <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-300 transition-colors">Start Investigation</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">Open Copilot workspace</div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400" />
                </button>
                <button className="flex items-center justify-between px-3 py-2.5 surface-1 hover:bg-orange-500/10 border border-white/[0.06] hover:border-orange-500/30 rounded-lg transition-fast group text-left">
                  <div>
                    <div className="text-xs font-medium text-slate-200 group-hover:text-orange-300 transition-colors">Find Related Intel</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">Query graph neighbors</div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-orange-400" />
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
