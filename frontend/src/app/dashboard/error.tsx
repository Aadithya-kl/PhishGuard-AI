"use client";

import { useEffect } from "react";
import { AlertOctagon, RefreshCcw } from "lucide-react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-slate-950 text-white p-6 text-center rounded-xl border border-white/5 shadow-2xl">
      <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-6">
        <AlertOctagon className="w-8 h-8 text-red-500" />
      </div>
      <h2 className="text-xl font-semibold mb-2">Telemetry Pipeline Offline</h2>
      <p className="text-slate-400 max-w-sm mb-8 text-sm">
        Failed to fetch dashboard metrics. The analytics service might be temporarily unavailable or rate-limited.
      </p>
      
      <button
        onClick={() => reset()}
        className="flex items-center gap-2 px-5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm font-medium transition-colors"
      >
        <RefreshCcw className="w-4 h-4" />
        Retry Connection
      </button>
    </div>
  );
}
