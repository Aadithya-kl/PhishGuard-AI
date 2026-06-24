"use client";

import { Bell, Search, ChevronDown, Command } from "lucide-react";
import { StatusIndicator } from "@/components/ui/status-indicator";

export function Header() {
  return (
    <header className="h-14 shrink-0 flex items-center justify-between px-6 liquid-glass border-b-0 border-l-0 border-r-0 border-t-0 z-10"
      style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
    >
      {/* Left: Org Switcher + Environment */}
      <div className="flex items-center gap-4">
        <button className="flex items-center gap-2 text-sm text-slate-300 hover:text-slate-100 transition-fast group">
          <div className="w-6 h-6 rounded bg-gradient-to-br from-violet-500/30 to-indigo-500/30 border border-white/[0.08] flex items-center justify-center text-[10px] font-bold text-indigo-300">
            P
          </div>
          <span className="font-medium">PhishGuard Corp</span>
          <ChevronDown className="w-3 h-3 text-slate-600 group-hover:text-slate-400 transition-fast" />
        </button>

        <div className="h-4 w-px bg-white/[0.06]" />

        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20">
          <StatusIndicator level="safe" size="sm" />
          <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider">
            Production
          </span>
        </div>

        <div className="h-4 w-px bg-white/[0.06]" />

        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/8 border border-amber-500/15">
          <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">
            Observation Mode
          </span>
        </div>
      </div>

      {/* Center: Search */}
      <button
        onClick={() => {
          // Trigger command palette
          const event = new KeyboardEvent("keydown", { key: "k", metaKey: true, ctrlKey: true, bubbles: true });
          document.dispatchEvent(event);
        }}
        className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.1] transition-fast text-slate-500 hover:text-slate-400 min-w-[260px]"
      >
        <Search className="w-3.5 h-3.5" />
        <span className="text-xs flex-1 text-left">Search or command...</span>
        <div className="flex items-center gap-0.5">
          <kbd className="px-1 py-0.5 text-[10px] font-medium bg-white/[0.04] border border-white/[0.06] rounded text-slate-600">
            <Command className="w-2.5 h-2.5 inline" />
          </kbd>
          <kbd className="px-1.5 py-0.5 text-[10px] font-medium bg-white/[0.04] border border-white/[0.06] rounded text-slate-600">
            K
          </kbd>
        </div>
      </button>

      {/* Right: Notifications + User */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/[0.03] transition-fast">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-[#020617]" />
        </button>

        <div className="h-4 w-px bg-white/[0.06]" />

        <button className="flex items-center gap-2 p-1 rounded-lg hover:bg-white/[0.03] transition-fast">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-[11px] font-semibold text-white">
            AU
          </div>
        </button>
      </div>
    </header>
  );
}
