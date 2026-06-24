import { Loader2 } from "lucide-react";

export default function DashboardLoading() {
  return (
    <div className="flex flex-col items-center justify-center h-full w-full bg-slate-950 text-white p-6 rounded-xl border border-white/5 shadow-2xl">
      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
      <h3 className="text-sm font-medium text-slate-300 tracking-wide">Syncing Telemetry...</h3>
    </div>
  );
}
