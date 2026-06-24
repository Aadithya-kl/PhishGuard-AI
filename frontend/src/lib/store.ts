// ============================================================================
// PhishGuard AI - Global State Store (Zustand)
// ============================================================================

import { create } from 'zustand';
import type { User, Notification, EmailScan } from '@/types';

interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setAuthenticated: (v: boolean) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (v: boolean) => void;

  // Notifications
  notifications: Notification[];
  setNotifications: (n: Notification[]) => void;
  markNotificationRead: (id: string) => void;
  unreadCount: () => number;

  // Active scan (for copilot context)
  activeScan: EmailScan | null;
  setActiveScan: (scan: EmailScan | null) => void;

  // Copilot
  copilotOpen: boolean;
  setCopilotOpen: (v: boolean) => void;
  toggleCopilot: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Auth
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setAuthenticated: (v) => set({ isAuthenticated: v }),

  // Sidebar
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),

  // Notifications
  notifications: [],
  setNotifications: (n) => set({ notifications: n }),
  markNotificationRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    })),
  unreadCount: () => get().notifications.filter((n) => !n.read).length,

  // Active scan
  activeScan: null,
  setActiveScan: (scan) => set({ activeScan: scan }),

  // Copilot
  copilotOpen: false,
  setCopilotOpen: (v) => set({ copilotOpen: v }),
  toggleCopilot: () => set((s) => ({ copilotOpen: !s.copilotOpen })),
}));
