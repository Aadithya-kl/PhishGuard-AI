/**
 * API client.
 *
 * Security model:
 *  - The access token lives only in memory (this module). Nothing sensitive is
 *    written to localStorage/sessionStorage, so an injected script cannot lift a
 *    long-lived credential from storage.
 *  - The refresh token is an HttpOnly cookie set by the backend; we just send
 *    `credentials: "include"` to /auth/refresh.
 *  - All requests are same-origin (/api is proxied by Next.js).
 */
import type {
  ApiKey, Campaign, CopilotTurn, DashboardStats, GraphPayload, Investigation, InvestigationDetail,
  Invite, IocDetail, LoginResult, Member, Paged, Recommendation, Report, RiskLevel, ScanDetail,
  ScanSummary, SearchItem, Session, TrendPoint,
} from "./types";

const BASE = "/api/v1";

let accessToken: string | null = null;
let refreshing: Promise<Session | null> | null = null;
let onSessionChange: ((s: Session | null) => void) | null = null;

export function bindSessionListener(fn: (s: Session | null) => void) {
  onSessionChange = fn;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function setSession(s: Session | null) {
  accessToken = s?.access_token ?? null;
  onSessionChange?.(s);
}

async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) return body.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ");
    if (typeof body?.error === "string") return body.error;
  } catch {
    /* not JSON */
  }
  if (res.status === 429) return "Too many requests. Wait a moment and try again.";
  if (res.status >= 500) return "The server hit an error. Try again, and check the backend logs if it keeps happening.";
  return `Request failed (${res.status})`;
}

/** Exchange the HttpOnly refresh cookie for a fresh access token. De-duplicated. */
export function refreshSession(): Promise<Session | null> {
  if (!refreshing) {
    refreshing = fetch(`${BASE}/auth/refresh`, { method: "POST", credentials: "include" })
      .then(async (res) => {
        if (!res.ok) {
          setSession(null);
          return null;
        }
        const s = (await res.json()) as Session;
        setSession(s);
        return s;
      })
      .catch(() => {
        setSession(null);
        return null;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

type Opts = Omit<RequestInit, "body"> & { body?: unknown; raw?: boolean };

async function request<T>(path: string, opts: Opts = {}, retried = false): Promise<T> {
  const headers = new Headers(opts.headers);
  let body: BodyInit | undefined;
  if (opts.body instanceof FormData) body = opts.body;
  else if (opts.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(opts.body);
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const res = await fetch(`${BASE}${path}`, { ...opts, headers, body, credentials: "same-origin" });

  if (res.status === 401 && !retried && !path.startsWith("/auth/login")) {
    const s = await refreshSession();
    if (s) return request<T>(path, opts, true);
    throw new ApiError(401, "Your session has ended. Sign in again.");
  }
  if (!res.ok) throw new ApiError(res.status, await readError(res));
  if (opts.raw) return res as unknown as T;
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const qs = (params: Record<string, string | number | undefined | null>) => {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  });
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const api = {
  auth: {
    async login(email: string, password: string, mfa_code?: string): Promise<LoginResult> {
      const res = await fetch(`${BASE}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, mfa_code: mfa_code || undefined }),
      });
      if (!res.ok) throw new ApiError(res.status, await readError(res));
      const data = (await res.json()) as LoginResult;
      if (!data.mfa_required && data.access_token) setSession(data as Session);
      return data;
    },
    async logout() {
      await fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "include" }).catch(() => undefined);
      setSession(null);
    },
    registerWithInvite: (invitation_token: string, full_name: string, password: string) =>
      request<{ message: string; email: string }>("/organizations/invites/register", {
        method: "POST",
        body: { invitation_token, full_name, password },
      }),
    changePassword: (current_password: string, new_password: string) =>
      request("/auth/change-password", { method: "POST", body: { current_password, new_password } }),
    totpSetup: () => request<{ secret: string; uri: string }>("/auth/totp/setup", { method: "POST" }),
    totpVerify: (code: string) => request("/auth/totp/verify", { method: "POST", body: { code } }),
    totpDisable: (password: string, code: string) => request("/auth/totp/disable", { method: "POST", body: { password, code } }),
    organizations: () => request<{ id: string; name: string; role: string }[]>("/auth/organizations"),
    async switchOrg(organization_id: string) {
      const s = await request<Session>("/auth/switch-org", { method: "POST", body: { organization_id } });
      setSession(s);
      return s;
    },
  },

  scans: {
    list: (p: { page?: number; risk_level?: RiskLevel | ""; status?: string; q?: string } = {}) =>
      request<Paged<ScanSummary>>(`/scans${qs({ page: p.page, risk_level: p.risk_level, status: p.status, q: p.q })}`),
    get: (id: string) => request<ScanDetail>(`/scans/${encodeURIComponent(id)}`),
    preview: (id: string) => request<{ sanitized_html: string; warnings: string[] }>(`/scans/${encodeURIComponent(id)}/preview`),
    rawHeaders: (id: string) => request<{ raw_headers: string }>(`/scans/${encodeURIComponent(id)}/raw-headers`),
    upload: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return request<{ id: string }>("/scans/upload", { method: "POST", body: fd });
    },
    paste: (raw: string) => {
      const fd = new FormData();
      fd.append("raw_content", raw);
      return request<{ id: string }>("/scans/paste", { method: "POST", body: fd });
    },
    rescan: (id: string) => request(`/scans/${encodeURIComponent(id)}/rescan`, { method: "POST" }),
    remove: (id: string) => request(`/scans/${encodeURIComponent(id)}`, { method: "DELETE" }),
  },

  dashboard: {
    stats: () => request<DashboardStats>("/dashboard/stats"),
    trends: (days = 14) => request<{ points: TrendPoint[] }>(`/dashboard/trends?days=${days}`),
    categories: () => request<{ categories: { name: string; count: number }[] }>("/dashboard/attack-categories"),
    topDomains: () => request<{ domains: { domain: string; count: number }[] }>("/dashboard/top-domains"),
    recent: () => request<ScanSummary[]>("/dashboard/recent-threats"),
  },

  hunt: {
    stats: () =>
      request<{
        top_domains: { domain: string; count: number }[];
        top_senders: { domain: string; count: number }[];
        common_attacks: { type: string; count: number }[];
        soc_metrics: Record<string, number>;
      }>("/threat-hunting/statistics"),
    search: (q: string) => request<{ total: number; results: SearchItem[] }>(`/threat-hunting/search${qs({ q })}`),
    ioc: (value: string) => request<IocDetail>(`/threat-hunting/ioc/${encodeURIComponent(value)}`),
    campaigns: () => request<{ total_campaigns: number; campaigns: Campaign[] }>("/threat-hunting/campaigns"),
  },

  investigations: {
    list: () => request<Investigation[]>("/investigations"),
    get: (id: string) => request<InvestigationDetail>(`/investigations/${encodeURIComponent(id)}`),
    create: (data: { title: string; description?: string; priority?: string; severity?: string }) =>
      request<{ id: string }>("/investigations", { method: "POST", body: data }),
    addArtifact: (id: string, artifact_type: string, artifact_value: string) =>
      request(`/investigations/${encodeURIComponent(id)}/artifacts`, { method: "POST", body: { artifact_type, artifact_value } }),
    addNote: (id: string, body: { content: string; status?: string; priority?: string; severity?: string }) =>
      request(`/investigations/${encodeURIComponent(id)}/notes`, { method: "POST", body }),
  },

  graph: {
    overview: (limit = 150) => request<GraphPayload>(`/graph/overview?limit=${limit}`),
    neighborhood: (ioc: string, depth = 2) => request<GraphPayload>(`/graph/neighborhood${qs({ ioc, depth })}`),
  },

  playbooks: {
    list: (status?: string) => request<Recommendation[]>(`/playbooks${qs({ status })}`),
    approve: (id: string, analyst_notes?: string) =>
      request(`/playbooks/${encodeURIComponent(id)}/approve`, { method: "POST", body: { analyst_notes } }),
    reject: (id: string, analyst_notes?: string) =>
      request(`/playbooks/${encodeURIComponent(id)}/reject`, { method: "POST", body: { analyst_notes } }),
  },

  reports: {
    generate: (target_id: string, report_type: "scan" | "investigation") =>
      request<Report>("/reports/generate", { method: "POST", body: { target_id, report_type, format: "pdf" } }),
    get: (id: string) => request<Report>(`/reports/${encodeURIComponent(id)}`),
    async download(id: string): Promise<Blob> {
      const res = await request<Response>(`/reports/${encodeURIComponent(id)}/download`, { raw: true });
      return res.blob();
    },
  },

  copilot: {
    chat: (message: string, history: CopilotTurn[], context: Record<string, string>) =>
      request<{ answer: string; tools_used: string[]; sources: string[]; confidence: number }>("/copilot/chat", {
        method: "POST",
        body: { message, history: history.slice(-20), context },
      }),
  },

  org: {
    members: () => request<Member[]>("/organizations/members"),
    updateMember: (id: string, body: { role?: string; is_active?: boolean }) =>
      request<Member>(`/organizations/members/${encodeURIComponent(id)}`, { method: "PATCH", body }),
    invites: () => request<Invite[]>("/organizations/invites"),
    invite: (email: string, role: string) => request<Invite>("/organizations/invites", { method: "POST", body: { email, role } }),
    revokeInvite: (id: string) => request(`/organizations/invites/${encodeURIComponent(id)}`, { method: "DELETE" }),
    apiKeys: () => request<ApiKey[]>("/api-keys"),
    createApiKey: (name: string, permissions: string[], expires_in_days: number) =>
      request<ApiKey & { raw_key: string }>("/api-keys", { method: "POST", body: { name, permissions, expires_in_days } }),
    revokeApiKey: (id: string) => request(`/api-keys/${encodeURIComponent(id)}`, { method: "DELETE" }),
  },
};
