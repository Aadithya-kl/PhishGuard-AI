"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Radar,
  Crosshair,
  Network,
  Zap,
  BarChart3,
  FileText,
  Settings,
  ChevronLeft,
  Activity,
  Search,
  Target,
} from "lucide-react";

const navGroups = [
  {
    label: "Intelligence",
    items: [
      { href: "/mission-control", label: "Mission Control", icon: Radar },
      { href: "/investigations", label: "Investigations", icon: Crosshair },
    ],
  },
  {
    label: "Operations",
    items: [
      { href: "/response", label: "Response", icon: Zap },
      { href: "/graph", label: "Knowledge Graph", icon: Network },
      { href: "/threat-hunting", label: "Threat Hunting", icon: Target },
    ],
  },
  {
    label: "Governance",
    items: [
      { href: "/executive", label: "Executive", icon: BarChart3 },
      { href: "/automation", label: "Automation", icon: Settings },
      { href: "/reports", label: "Reports", icon: FileText },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(true);

  const width = collapsed ? 68 : 240;

  return (
    <motion.aside
      animate={{ width }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      onMouseEnter={() => setCollapsed(false)}
      onMouseLeave={() => setCollapsed(true)}
      className="h-screen flex flex-col border-r border-white/[0.04] bg-[#020617]/95 relative z-20 shrink-0 overflow-hidden"
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 gap-3 shrink-0 border-b border-white/[0.04]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shrink-0">
          <Shield className="w-4 h-4 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="font-semibold text-sm text-slate-200 tracking-tight whitespace-nowrap"
            >
              PhishGuard <span className="text-indigo-400">AI</span>
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 flex flex-col gap-6 overflow-y-auto overflow-x-hidden">
        {navGroups.map((group) => (
          <div key={group.label}>
            <AnimatePresence>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.1 }}
                  className="text-[10px] font-semibold text-slate-600 uppercase tracking-[0.12em] px-2.5 mb-2"
                >
                  {group.label}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex flex-col gap-0.5">
              {group.items.map((link) => {
                const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
                const Icon = link.icon;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative flex items-center gap-3 rounded-lg transition-fast group ${
                      collapsed ? "justify-center px-0 py-2.5 mx-1" : "px-2.5 py-2"
                    } ${
                      isActive
                        ? "bg-indigo-500/10 text-indigo-400"
                        : "text-slate-500 hover:text-slate-300 hover:bg-white/[0.03]"
                    }`}
                  >
                    {/* Active indicator bar */}
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active"
                        className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-full bg-gradient-to-b from-indigo-400 to-violet-500"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}

                    <Icon className={`w-[18px] h-[18px] shrink-0 ${isActive ? "text-indigo-400" : ""}`} />

                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, x: -4 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -4 }}
                          transition={{ duration: 0.12 }}
                          className="text-[13px] font-medium whitespace-nowrap"
                        >
                          {link.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom: User */}
      <div className="shrink-0 p-3 border-t border-white/[0.04]">
        <div className={`flex items-center gap-3 ${collapsed ? "justify-center" : ""}`}>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-600 flex items-center justify-center text-xs font-semibold text-slate-300 shrink-0 border border-white/[0.08]">
            A
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.12 }}
                className="flex-1 min-w-0"
              >
                <p className="text-xs font-medium text-slate-300 truncate">Admin User</p>
                <p className="text-[10px] text-slate-600 truncate">admin@phishguard.ai</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.aside>
  );
}

export default Sidebar;
