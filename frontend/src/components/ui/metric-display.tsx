"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

interface MetricDisplayProps {
  label: string;
  value: number | string;
  suffix?: string;
  prefix?: string;
  trend?: { direction: "up" | "down" | "flat"; value: string };
  trendSentiment?: "positive" | "negative" | "neutral";
  size?: "sm" | "md" | "lg";
  animate?: boolean;
  className?: string;
}

export function MetricDisplay({
  label,
  value,
  suffix = "",
  prefix = "",
  trend,
  trendSentiment = "neutral",
  size = "md",
  animate = true,
  className,
}: MetricDisplayProps) {
  const [displayValue, setDisplayValue] = useState(animate && typeof value === "number" ? 0 : value);

  useEffect(() => {
    if (!animate || typeof value !== "number") {
      setDisplayValue(value);
      return;
    }

    const duration = 800;
    const startTime = Date.now();
    const startValue = 0;
    const endValue = value;

    const tick = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(startValue + (endValue - startValue) * eased);
      setDisplayValue(current);
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  }, [value, animate]);

  const sizeClasses = {
    sm: "text-xl font-semibold",
    md: "text-3xl font-light tracking-tight",
    lg: "text-display",
  };

  const trendColors = {
    positive: "text-emerald-400",
    negative: "text-red-400",
    neutral: "text-slate-500",
  };

  const TrendIcon =
    trend?.direction === "up" ? ArrowUpRight :
    trend?.direction === "down" ? ArrowDownRight : Minus;

  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 8 } : undefined}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className={cn("flex flex-col gap-1.5", className)}
    >
      <span className="text-label">{label}</span>

      <div className="flex items-baseline gap-1">
        {prefix && <span className={cn(sizeClasses[size], "text-slate-500")}>{prefix}</span>}
        <span className={cn(sizeClasses[size], "text-slate-100 tabular-nums")}>
          {displayValue}
        </span>
        {suffix && <span className={cn("text-sm font-medium text-slate-500")}>{suffix}</span>}
      </div>

      {trend && (
        <div className={cn("flex items-center gap-1 text-xs", trendColors[trendSentiment])}>
          <TrendIcon className="w-3.5 h-3.5" />
          <span>{trend.value}</span>
        </div>
      )}
    </motion.div>
  );
}
