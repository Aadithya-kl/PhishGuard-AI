"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface MitreTechnique {
  id: string;
  name: string;
  coverage: number; // 0-100
  detections: number;
}

interface MitreTactic {
  id: string;
  name: string;
  techniques: MitreTechnique[];
}

interface MitreHeatmapProps {
  tactics: MitreTactic[];
}

export function MitreHeatmap({ tactics }: MitreHeatmapProps) {
  const [hoveredTechnique, setHoveredTechnique] = useState<MitreTechnique | null>(null);

  const getColorClass = (coverage: number) => {
    if (coverage === 0) return "bg-slate-800/30 border-white/[0.03]";
    if (coverage < 30) return "bg-indigo-900/20 border-indigo-500/20 text-indigo-200";
    if (coverage < 70) return "bg-indigo-800/40 border-indigo-500/40 text-indigo-100";
    return "bg-indigo-600/60 border-indigo-400/60 text-white shadow-[0_0_10px_rgba(99,102,241,0.2)]";
  };

  return (
    <div className="w-full h-full overflow-x-auto pb-4">
      <div className="flex gap-2 min-w-max">
        {tactics.map((tactic) => (
          <div key={tactic.id} className="flex flex-col w-32 shrink-0">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 truncate px-1" title={tactic.name}>
              {tactic.name}
            </div>
            <div className="flex flex-col gap-1.5">
              {tactic.techniques.map((tech) => (
                <motion.div
                  key={tech.id}
                  className={cn(
                    "h-10 rounded border flex items-center px-2 cursor-pointer transition-colors relative overflow-hidden",
                    getColorClass(tech.coverage)
                  )}
                  whileHover={{ scale: 1.05, zIndex: 10 }}
                  onMouseEnter={() => setHoveredTechnique(tech)}
                  onMouseLeave={() => setHoveredTechnique(null)}
                >
                  <span className="text-[9px] font-medium truncate leading-tight w-full z-10" style={{ opacity: tech.coverage > 0 ? 1 : 0.3 }}>
                    {tech.name}
                  </span>
                  
                  {/* Hover tooltip for the technique */}
                  <AnimatePresence>
                    {hoveredTechnique?.id === tech.id && (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-[#0f172a] border border-white/10 rounded-lg shadow-xl p-2 z-50 pointer-events-none"
                      >
                        <div className="text-[10px] text-slate-400 mb-1">{tech.id}</div>
                        <div className="text-xs font-semibold text-white mb-2">{tech.name}</div>
                        <div className="flex justify-between text-[10px]">
                          <span className="text-slate-400">Coverage:</span>
                          <span className="text-indigo-300 font-medium">{tech.coverage}%</span>
                        </div>
                        <div className="flex justify-between text-[10px]">
                          <span className="text-slate-400">Detections:</span>
                          <span className="text-indigo-300 font-medium">{tech.detections}</span>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
