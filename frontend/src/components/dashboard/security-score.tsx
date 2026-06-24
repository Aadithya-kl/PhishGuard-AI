"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface SecurityScoreProps {
  score: number; // 0-100
  trend?: "up" | "down" | "flat";
  size?: number;
}

export function SecurityScore({ score, trend = "flat", size = 200 }: SecurityScoreProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const duration = 1200;
    const startTime = Date.now();
    const tick = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4); // easeOutQuart
      setDisplayScore(Math.round(score * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [score]);

  const strokeWidth = size * 0.08;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  // Use a semi-circle gauge (actually 270 degrees)
  const arcLength = circumference * 0.75;
  const offset = circumference - (displayScore / 100) * arcLength;

  let colorClass = "text-emerald-400";
  let glowClass = "drop-shadow-[0_0_12px_rgba(52,211,153,0.5)]";
  if (score < 60) {
    colorClass = "text-red-400";
    glowClass = "drop-shadow-[0_0_12px_rgba(248,113,113,0.5)]";
  } else if (score < 80) {
    colorClass = "text-amber-400";
    glowClass = "drop-shadow-[0_0_12px_rgba(251,191,36,0.5)]";
  }

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rotate-[135deg]">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-slate-800"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        {/* Foreground track */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className={cn(colorClass, glowClass)}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-1">
          Posture
        </span>
        <div className={cn("text-display font-light tabular-nums", colorClass, glowClass)}>
          {displayScore}
        </div>
        <span className="text-slate-500 text-xs mt-1">/ 100</span>
      </div>
    </div>
  );
}
