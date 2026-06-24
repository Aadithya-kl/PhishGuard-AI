"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Search,
  Network,
  FileText,
  Shield,
  Activity,
  Brain,
  Crosshair,
  BarChart3,
  Zap,
  Command,
} from "lucide-react";

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  action: () => void;
  group: string;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const commands: CommandItem[] = [
    { id: "mission", label: "Mission Control", description: "Security overview", icon: <Shield className="w-4 h-4" />, action: () => router.push("/mission-control"), group: "Navigate" },
    { id: "graph", label: "Knowledge Graph", description: "Threat intelligence graph", icon: <Network className="w-4 h-4" />, action: () => router.push("/graph"), group: "Navigate" },
    { id: "investigations", label: "Investigations", description: "Active investigations", icon: <Crosshair className="w-4 h-4" />, action: () => router.push("/investigations"), group: "Navigate" },
    { id: "response", label: "Active Response", description: "Response center", icon: <Zap className="w-4 h-4" />, action: () => router.push("/response"), group: "Navigate" },
    { id: "executive", label: "Executive Dashboard", description: "Security posture", icon: <BarChart3 className="w-4 h-4" />, action: () => router.push("/executive"), group: "Navigate" },
    { id: "reports", label: "Reports", description: "Generate reports", icon: <FileText className="w-4 h-4" />, action: () => router.push("/reports"), group: "Navigate" },
    { id: "search_ioc", label: "Search IOC", description: "Look up indicator of compromise", icon: <Search className="w-4 h-4" />, action: () => router.push("/graph"), group: "Actions" },
    { id: "launch_copilot", label: "Launch Copilot", description: "AI Security Console", icon: <Brain className="w-4 h-4" />, action: () => {}, group: "Actions" },
    { id: "simulate", label: "Simulate Response", description: "Dry run an action", icon: <Activity className="w-4 h-4" />, action: () => router.push("/response"), group: "Actions" },
  ];

  const filtered = query
    ? commands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          (c.description && c.description.toLowerCase().includes(query.toLowerCase()))
      )
    : commands;

  const groups = Array.from(new Set(filtered.map((c) => c.group)));

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
        setQuery("");
        setSelectedIndex(0);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    },
    []
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  const executeCommand = (cmd: CommandItem) => {
    cmd.action();
    setOpen(false);
    setQuery("");
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-[560px] max-h-[420px] liquid-glass-elevated rounded-2xl overflow-hidden flex flex-col"
          >
            {/* Search input */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/[0.06]">
              <Search className="w-4 h-4 text-slate-500 shrink-0" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                onKeyDown={(e) => {
                  if (e.key === "ArrowDown") {
                    e.preventDefault();
                    setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
                  } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    setSelectedIndex((i) => Math.max(i - 1, 0));
                  } else if (e.key === "Enter" && filtered[selectedIndex]) {
                    executeCommand(filtered[selectedIndex]);
                  }
                }}
                placeholder="Type a command or search..."
                className="flex-1 bg-transparent text-sm text-slate-200 placeholder:text-slate-600 outline-none"
              />
              <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 bg-white/[0.04] border border-white/[0.06] rounded">
                ESC
              </kbd>
            </div>

            {/* Results */}
            <div className="flex-1 overflow-y-auto py-2 px-2">
              {filtered.length === 0 && (
                <div className="px-4 py-8 text-center text-sm text-slate-600">
                  No commands found
                </div>
              )}

              {groups.map((group) => (
                <div key={group}>
                  <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">
                    {group}
                  </div>
                  {filtered
                    .filter((c) => c.group === group)
                    .map((cmd) => {
                      const globalIdx = filtered.indexOf(cmd);
                      return (
                        <button
                          key={cmd.id}
                          onClick={() => executeCommand(cmd)}
                          onMouseEnter={() => setSelectedIndex(globalIdx)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-fast ${
                            globalIdx === selectedIndex
                              ? "bg-indigo-500/10 text-slate-200"
                              : "text-slate-400 hover:text-slate-300"
                          }`}
                        >
                          <span className={globalIdx === selectedIndex ? "text-indigo-400" : "text-slate-500"}>
                            {cmd.icon}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{cmd.label}</div>
                            {cmd.description && (
                              <div className="text-xs text-slate-600 truncate">{cmd.description}</div>
                            )}
                          </div>
                        </button>
                      );
                    })}
                </div>
              ))}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
