"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

export default function GraphError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Graph visualization error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-black/40 text-white p-6 text-center">
      <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-6">
        <AlertTriangle className="w-8 h-8 text-red-500" />
      </div>
      <h2 className="text-2xl font-semibold mb-2">Visualization Engine Failed</h2>
      <p className="text-slate-400 max-w-md mb-8">
        We encountered an error while rendering the intelligence graph. This may be due to a network interruption or corrupted session state.
      </p>
      
      <div className="flex gap-4">
        <button
          onClick={() => reset()}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
        >
          <RefreshCcw className="w-4 h-4" />
          Reload Graph
        </button>
      </div>
    </div>
  );
}
