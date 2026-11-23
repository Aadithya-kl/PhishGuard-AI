"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, bindSessionListener, refreshSession } from "./api";
import type { Session } from "./types";

type State = { status: "loading" | "signed-in" | "signed-out"; session: Session | null };

const Ctx = createContext<{
  state: State;
  signOut: () => Promise<void>;
  can: (perm: Perm) => boolean;
} | null>(null);

// Mirrors backend ROLE_PERMISSIONS for showing/hiding UI. The backend still enforces everything.
type Perm = "upload" | "delete" | "investigate" | "reports" | "copilot" | "manage_org";
const ROLE_PERMS: Record<string, Perm[]> = {
  "Platform Admin": ["upload", "delete", "investigate", "reports", "copilot", "manage_org"],
  "Organization Admin": ["upload", "delete", "investigate", "reports", "copilot", "manage_org"],
  "SOC Manager": ["upload", "delete", "investigate", "reports", "copilot"],
  "SOC Analyst": ["upload", "investigate", "reports", "copilot"],
  "Read Only Analyst": [],
};

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<State>({ status: "loading", session: null });

  useEffect(() => {
    bindSessionListener((s) => setState({ status: s ? "signed-in" : "signed-out", session: s }));
    refreshSession();
  }, []);

  // Refresh a minute before the access token expires.
  useEffect(() => {
    if (!state.session) return;
    const ms = Math.max(30_000, (state.session.expires_in - 60) * 1000);
    const t = setTimeout(() => refreshSession(), ms);
    return () => clearTimeout(t);
  }, [state.session]);

  const signOut = useCallback(async () => {
    await api.auth.logout();
  }, []);

  const can = useCallback(
    (perm: Perm) => (ROLE_PERMS[state.session?.organization?.role ?? ""] ?? []).includes(perm),
    [state.session],
  );

  const value = useMemo(() => ({ state, signOut, can }), [state, signOut, can]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSession must be used inside SessionProvider");
  return v;
}
