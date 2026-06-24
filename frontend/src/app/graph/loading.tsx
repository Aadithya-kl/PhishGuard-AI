import { Loader2 } from "lucide-react";

export default function GraphLoading() {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-black/40 text-white">
      <div className="relative">
        <div className="absolute inset-0 rounded-full blur-xl bg-indigo-500/30 animate-pulse"></div>
        <Loader2 className="w-12 h-12 text-indigo-400 animate-spin relative z-10" />
      </div>
      <h3 className="mt-6 text-lg font-medium tracking-wide">Initializing Intelligence Engine</h3>
      <p className="text-sm text-slate-400 mt-2">Loading topology and rendering spatial coordinates...</p>
    </div>
  );
}
