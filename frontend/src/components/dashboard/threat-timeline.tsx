"use client";

import React from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { format } from "date-fns";

interface ThreatTimelineProps {
  data: any[];
}

export function ThreatTimeline({ data }: ThreatTimelineProps) {
  return (
    <div className="w-full h-full min-h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorSafe" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34d399" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(val) => format(new Date(val), "HH:mm")} 
            stroke="rgba(255,255,255,0.1)"
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickMargin={10}
            axisLine={false}
          />
          <YAxis 
            stroke="rgba(255,255,255,0.1)"
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickMargin={10}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: "rgba(15, 23, 42, 0.9)", 
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)"
            }}
            itemStyle={{ color: "#e2e8f0", fontSize: "12px" }}
            labelStyle={{ color: "#94a3b8", fontSize: "10px", marginBottom: "4px" }}
            labelFormatter={(val) => format(new Date(val), "MMM d, yyyy HH:mm")}
          />
          <Area 
            type="monotone" 
            dataKey="threats" 
            stroke="#818cf8" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorThreats)" 
            animationDuration={1500}
            animationEasing="ease-out"
          />
          <Area 
            type="monotone" 
            dataKey="safe" 
            stroke="#34d399" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorSafe)" 
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
