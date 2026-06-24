"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface IntelCardProps {
  children: React.ReactNode;
  className?: string;
  accentColor?: "indigo" | "critical" | "safe" | "amber" | "none";
  accentPosition?: "top" | "left" | "none";
  interactive?: boolean;
  onClick?: () => void;
}

export function IntelCard({
  children,
  className,
  accentColor = "none",
  accentPosition = "none",
  interactive = false,
  onClick,
}: IntelCardProps) {
  const accentGradients: Record<string, string> = {
    indigo: "from-indigo-500 to-violet-500",
    critical: "from-red-500 to-rose-500",
    safe: "from-emerald-500 to-teal-500",
    amber: "from-amber-500 to-yellow-500",
    none: "",
  };

  return (
    <motion.div
      onClick={onClick}
      whileHover={interactive ? { y: -2, transition: { duration: 0.2 } } : undefined}
      className={cn(
        "relative rounded-xl overflow-hidden",
        interactive ? "surface-interactive cursor-pointer" : "surface-0",
        className
      )}
    >
      {/* Top accent strip */}
      {accentPosition === "top" && accentColor !== "none" && (
        <div
          className={cn(
            "absolute top-0 left-3 right-3 h-[2px] rounded-b-full bg-gradient-to-r",
            accentGradients[accentColor]
          )}
        />
      )}

      {/* Left accent strip */}
      {accentPosition === "left" && accentColor !== "none" && (
        <div
          className={cn(
            "absolute left-0 top-3 bottom-3 w-[2px] rounded-r-full bg-gradient-to-b",
            accentGradients[accentColor]
          )}
        />
      )}

      {children}
    </motion.div>
  );
}
