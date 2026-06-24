import { CopilotMessage, CopilotResponse, DashboardStats, RiskDistribution, TrendData, AttackCategory, TopDomain, EmailScan, AuditLogEntry, User, LoginRequest, RegisterRequest, LoginResponse, ApiKey, Notification, Report, GraphData } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getTokens() {
  if (typeof window === 'undefined') return { access: null, refresh: null };
  return {
    access: localStorage.getItem('phishguard_token'),
    refresh: localStorage.getItem('phishguard_refresh_token')
  };
}

function setTokens(access: string, refresh: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('phishguard_token', access);
  localStorage.setItem('phishguard_refresh_token', refresh);
}

function clearTokens() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('phishguard_token');
  localStorage.removeItem('phishguard_refresh_token');
}

function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const user = localStorage.getItem('phishguard_user');
  return user ? JSON.parse(user) : null;
}

function setUser(user: User) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('phishguard_user', JSON.stringify(user));
}

async function tryRefreshToken(): Promise<boolean> {
  const { refresh } = getTokens();
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (res.ok) {
      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    }
  } catch {
    // ignore
  }
  return false;
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const { access } = getTokens();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {})
  };
  if (access) headers['Authorization'] = `Bearer ${access}`;

  let res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) {
    if (await tryRefreshToken()) {
      const newAccess = getTokens().access;
      headers['Authorization'] = `Bearer ${newAccess}`;
      res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } else {
      clearTokens();
      if (typeof window !== 'undefined') window.location.href = '/';
      throw new Error('Unauthorized');
    }
  }
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

async function apiFetchFormData<T>(endpoint: string, formData: FormData): Promise<T> {
  const { access } = getTokens();
  const headers: Record<string, string> = {};
  if (access) headers['Authorization'] = `Bearer ${access}`;

  let res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
  });
  
  if (res.status === 401) {
    if (await tryRefreshToken()) {
      const newAccess = getTokens().access;
      headers['Authorization'] = `Bearer ${newAccess}`;
      res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
      });
    } else {
      clearTokens();
      if (typeof window !== 'undefined') window.location.href = '/';
      throw new Error('Unauthorized');
    }
  }
  
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  auth: {
    login: (creds: LoginRequest) => apiFetch<LoginResponse>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(creds) }),
    register: (data: RegisterRequest) => apiFetch<LoginResponse>('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    getMe: () => apiFetch<User>('/api/v1/auth/me'),
    createApiKey: (name: string) => apiFetch<ApiKey & { full_key: string }>('/api/v1/auth/api-keys', { method: 'POST', body: JSON.stringify({ name }) }),
    listApiKeys: () => apiFetch<ApiKey[]>('/api/v1/auth/api-keys'),
    deleteApiKey: (keyId: string) => apiFetch<void>(`/api/v1/auth/api-keys/${keyId}`, { method: 'DELETE' }),
    logout: () => { clearTokens(); if (typeof window !== 'undefined') window.location.href = '/'; }
  },
  scans: {
    upload: (file: File) => { const fd = new FormData(); fd.append('file', file); return apiFetchFormData<EmailScan>('/api/v1/scans/upload', fd); },
    paste: (content: string) => { const fd = new FormData(); fd.append('raw_content', content); return apiFetchFormData<EmailScan>('/api/v1/scans/paste', fd); },
    submitHeaders: (headers: string) => apiFetch<EmailScan>('/api/v1/scan/headers', { method: 'POST', body: JSON.stringify({ headers }) }),
    list: (page = 1, perPage = 20) => apiFetch<{ scans: EmailScan[]; total: number }>(`/api/v1/scans?page=${page}&per_page=${perPage}`),
    getById: (id: string) => apiFetch<EmailScan>(`/api/v1/scans/${id}`),
    getSandbox: (id: string) => apiFetch<{ sanitized_html: string; raw_source: string; suspicious_elements: string[] }>(`/api/v1/scans/${id}/sandbox`),
    delete: (id: string) => apiFetch<void>(`/api/v1/scans/${id}`, { method: 'DELETE' }),
  },
  dashboard: {
    getStats: () => apiFetch<DashboardStats>('/api/v1/dashboard/stats'),
    getTrends: (days = 30) => apiFetch<TrendData[]>(`/api/v1/dashboard/trends?days=${days}`),
    getRiskDistribution: () => apiFetch<RiskDistribution>('/api/v1/dashboard/risk-distribution'),
    getAttackCategories: () => apiFetch<AttackCategory[]>('/api/v1/dashboard/attack-categories'),
    getTopDomains: () => apiFetch<TopDomain[]>('/api/v1/dashboard/top-domains'),
    getRecentScans: (limit = 10) => apiFetch<EmailScan[]>(`/api/v1/dashboard/recent-scans?limit=${limit}`),
  },
  hunt: {
    getStatistics: () => apiFetch<any>('/api/v1/threat-hunting/statistics'),
    search: (query: string) => apiFetch<any>(`/api/v1/threat-hunting/search?q=${encodeURIComponent(query)}`),
    getIocDetails: (value: string) => apiFetch<any>(`/api/v1/threat-hunting/ioc/${encodeURIComponent(value)}`),
    getCampaigns: () => apiFetch<any>('/api/v1/threat-hunting/campaigns'),
    getSavedSearches: () => apiFetch<any>('/api/v1/threat-hunting/saved-searches'),
    saveSearch: (name: string, query: string) => apiFetch<any>(`/api/v1/threat-hunting/saved-searches?name=${encodeURIComponent(name)}&query=${encodeURIComponent(query)}`, { method: 'POST' }),
    getTrackedEntities: () => apiFetch<any>('/api/v1/threat-hunting/tracked-entities'),
    trackEntity: (type: string, value: string) => apiFetch<any>(`/api/v1/threat-hunting/tracked-entities?entity_type=${type}&entity_value=${encodeURIComponent(value)}`, { method: 'POST' }),
  },
  investigations: {
    list: () => apiFetch<any>('/api/v1/investigations'),
    getById: (id: string) => apiFetch<any>(`/api/v1/investigations/${id}`),
    create: (data: any) => apiFetch<any>('/api/v1/investigations', { method: 'POST', body: JSON.stringify(data) }),
    addArtifact: (id: string, artifact_type: string, artifact_value: string) => apiFetch<any>(`/api/v1/investigations/${id}/artifacts`, { method: 'POST', body: JSON.stringify({ artifact_type, artifact_value }) }),
    addNote: (id: string, content: string, status?: string, priority?: string, severity?: string) => apiFetch<any>(`/api/v1/investigations/${id}/notes`, { method: 'POST', body: JSON.stringify({ content, status, priority, severity }) }),
  },
  reports: {
    generate: (targetId: string, type: string, format: string, graphSnapshot?: string) => apiFetch<Report>('/api/v1/reports/generate', { method: 'POST', body: JSON.stringify({ target_id: targetId, report_type: type, format, graph_snapshot: graphSnapshot }) }),
    list: () => apiFetch<Report[]>('/api/v1/reports'),
    getById: (id: string) => apiFetch<Report>(`/api/v1/reports/${id}`),
    download: async (reportId: string) => {
      const { access } = getTokens();
      const res = await fetch(`${API_BASE}/api/v1/reports/${reportId}/download`, { headers: access ? { Authorization: `Bearer ${access}` } : {} });
      if (!res.ok) throw new Error('Download failed');
      return res.blob();
    },
  },
  copilot: {
    chat: (message: string, history: CopilotMessage[], analystMode: string = "soc_analyst", context: Record<string, string> = {}) => apiFetch<CopilotResponse & { tools_used?: string[], sources?: string[], confidence?: number }>('/api/v1/copilot/chat', { method: 'POST', body: JSON.stringify({ message, history, analyst_mode: analystMode, context }) }),
    getSuggestions: (scanId?: string) => apiFetch<string[]>(`/api/v1/copilot/suggestions${scanId ? `?scan_id=${scanId}` : ''}`),
  },
  graph: {
    getScanGraph: (scanId: string) => apiFetch<GraphData>(`/api/v1/graph/scan/${scanId}`),
    getFullGraph: () => apiFetch<GraphData>('/api/v1/graph'),
    getNodeDetails: (nodeId: string) => apiFetch<Record<string, any>>(`/api/v1/graph/node/${nodeId}`),
    getAttackChain: (scanId: string) => apiFetch<GraphData>(`/api/v1/graph/attack-chain/${scanId}`),
  },
  admin: {
    getUsers: () => apiFetch<User[]>('/api/v1/admin/users'),
    updateUserRole: (userId: string, role: string) => apiFetch<void>(`/api/v1/admin/users/${userId}/role`, { method: 'PUT', body: JSON.stringify({ role }) }),
    getAuditLog: () => apiFetch<AuditLogEntry[]>('/api/v1/admin/audit-log'),
  },
  notifications: {
    list: () => apiFetch<Notification[]>('/api/v1/notifications'),
    markRead: (id: string) => apiFetch<void>(`/api/v1/notifications/${id}/read`, { method: 'PUT' }),
  },
};

// Aliasing getToken for backwards compatibility
export { getTokens as getToken, getUser, clearTokens, setUser, setTokens };
