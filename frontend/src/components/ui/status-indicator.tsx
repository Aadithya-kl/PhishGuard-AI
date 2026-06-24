"use client";

import React from "react";
import { cn } from "@/lib/utils";

type StatusLevel = "safe" | "low" | "medium" | "high" | "critical" | "info" | "active";

interface StatusIndicatorProps {
  level: StatusLevel;
  label?: string;
  pulse?: boolean;
  size?: "sm" | "md" | "lg";
  variant?: "dot" | "badge";
  className?: string;
}

const statusConfig: Record<StatusLevel, { color: string; bg: string; glow: string; text: string }> = {
  safe:     { color: "bg-emerald-400", bg: "bg-emerald-400/10", glow: "shadow-[0_0_8px_rgba(52,211,153,0.5)]", text: "text-emerald-400" },
  low:      { color: "bg-sky-400",     bg: "bg-sky-400/10",     glow: "shadow-[0_0_8px_rgba(56,189,248,0.5)]",  text: "text-sky-400" },
  medium:   { color: "bg-amber-400",   bg: "bg-amber-400/10",   glow: "shadow-[0_0_8px_rgba(251,191,36,0.5)]",  text: "text-amber-400" },
  high:     { color: "bg-orange-400",  bg: "bg-orange-400/10",  glow: "shadow-[0_0_8px_rgba(251,146,60,0.5)]",  text: "text-orange-400" },
  critical: { color: "bg-red-400",     bg: "bg-red-400/10",     glow: "shadow-[0_0_8px_rgba(248,113,113,0.5)]", text: "text-red-400" },
  info:     { color: "bg-indigo-400",  bg: "bg-indigo-400/10",  glow: "shadow-[0_0_8px_rgba(129,140,248,0.5)]", text: "text-indigo-400" },
  active:   { color: "bg-cyan-400",    bg: "bg-cyan-400/10",    glow: "shadow-[0_0_8px_rgba(34,211,238,0.5)]",  text: "text-cyan-400" },
};

const dotSizes = { sm: "w-1.5 h-1.5", md: "w-2 h-2", lg: "w-2.5 h-2.5" };

export function StatusIndicator({
  level,
  label,
  pulse = false,
  size = "md",
  variant = "dot",
  className,
}: StatusIndicatorProps) {
  const config = statusConfig[level];

  if (variant === "badge") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium tracking-wide uppercase",
          config.bg,
          config.text,
          "border",
          `border-current/20`,
          className
        )}
      >
        <span className={cn("rounded-full", dotSizes.sm, config.color, pulse && "animate-pulse-glow")} />
        {label || level}
      </span>
    );
  }

  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span
        className={cn(
          "rounded-full",
          dotSizes[size],
          config.color,
          pulse && config.glow,
          pulse && "animate-pulse-glow"
        )}
      />
      {label && <span className={cn("text-xs", config.text)}>{label}</span>}
    </span>
  );
}
