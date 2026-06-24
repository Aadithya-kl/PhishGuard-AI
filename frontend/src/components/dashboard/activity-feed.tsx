"use client";

import React from "react";
import { motion } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { AlertCircle, ShieldAlert, Zap, Search } from "lucide-react";
import { StatusIndicator } from "@/components/ui/status-indicator";

interface ActivityEvent {
  id: string;
  type: "detection" | "investigation" | "response" | "intel";
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  timestamp: string;
}

interface ActivityFeedProps {
  events: ActivityEvent[];
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  const getIcon = (type: string, severity: string) => {
    switch (type) {
      case "detection": return <ShieldAlert className="w-4 h-4 text-orange-400" />;
      case "investigation": return <Search className="w-4 h-4 text-indigo-400" />;
      case "response": return <Zap className="w-4 h-4 text-cyan-400" />;
      default: return <AlertCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusLevel = (severity: string): any => {
    if (severity === "critical") return "critical";
    if (severity === "high") return "high";
    if (severity === "medium") return "medium";
    if (severity === "low") return "low";
    return "info";
  };

  return (
    <div className="flex flex-col gap-4">
      {events.map((event, i) => (
        <motion.div
          key={event.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: i * 0.1 }}
          className="flex gap-4 group"
        >
          {/* Timeline track & node */}
          <div className="flex flex-col items-center relative">
            <div className="w-8 h-8 rounded-full surface-1 border border-white/10 flex items-center justify-center z-10 shadow-lg group-hover:border-indigo-500/50 transition-colors">
              {getIcon(event.type, event.severity)}
            </div>
            {i !== events.length - 1 && (
              <div className="absolute top-8 bottom-[-16px] w-[2px] bg-gradient-to-b from-white/10 to-transparent" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 pb-4">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <StatusIndicator level={getStatusLevel(event.severity)} size="sm" pulse={event.severity === "critical"} />
                <span className="text-sm font-medium text-slate-200">{event.title}</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              {event.description}
            </p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
