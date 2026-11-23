export type RiskLevel = "safe" | "low" | "suspicious" | "high";
export type ScanStatus = "pending" | "analyzing" | "completed" | "failed";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  mfa_enabled: boolean;
  created_at: string;
}

export interface OrgSummary {
  id: string;
  name: string;
  role: string;
}

export interface Session {
  access_token: string;
  expires_in: number;
  user: User;
  organization: OrgSummary | null;
}

export interface LoginResult extends Partial<Session> {
  mfa_required: boolean;
}

export interface ScanSummary {
  id: string;
  subject: string;
  sender_address: string;
  sender_display_name: string;
  recipient: string;
  overall_risk_score: number;
  risk_level: RiskLevel;
  attack_type: string | null;
  status: ScanStatus;
  scanned_at: string;
}

export interface Evidence {
  type?: string;
  description?: string;
  severity?: string;
  evidence?: string[] | string;
  [k: string]: unknown;
}

export interface HeaderAnalysis {
  spf_pass: boolean | null;
  spf_result: string;
  dkim_pass: boolean | null;
  dkim_result: string;
  dmarc_pass: boolean | null;
  dmarc_result: string;
  sender_spoofed: boolean;
  display_name_impersonation: boolean;
  domain_mismatch: boolean;
  trust_score: number;
  evidence: Evidence[] | null;
}

export interface UrlAnalysis {
  id: string;
  original_url: string;
  domain: string;
  risk_score: number;
  is_shortened: boolean;
  is_homoglyph: boolean;
  is_typosquatting: boolean;
  is_ip_based: boolean;
  evidence: Evidence[] | null;
}

export interface AttachmentAnalysis {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  md5_hash: string;
  sha256_hash: string;
  is_executable: boolean;
  has_macros: boolean;
  is_double_extension: boolean;
  threat_score: number;
}

export interface AiAnalysis {
  model_used: string;
  attack_classification: string;
  confidence_score: number;
  severity_level: string;
  reasoning: string;
  tactics_detected: { tactic?: string; description?: string; confidence?: number; evidence?: string }[] | null;
  recommended_actions: string[] | null;
}

export interface Ioc {
  id: string;
  ioc_type: string;
  value: string;
  threat_score: number;
}

export interface Detection {
  detection_name?: string;
  severity?: string;
  confidence?: number;
  description?: string;
  mitre?: { technique_id?: string; name?: string }[];
  [k: string]: unknown;
}

export interface ScanDetail extends ScanSummary {
  reply_to: string | null;
  return_path: string | null;
  body_text: string;
  risk_breakdown: Record<string, number | string> | null;
  header_analysis: HeaderAnalysis | null;
  url_analyses: UrlAnalysis[] | null;
  attachment_analyses: AttachmentAnalysis[] | null;
  ai_analysis: AiAnalysis | null;
  detections: Detection[] | null;
  iocs: Ioc[] | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardStats {
  total_scans: number;
  threats_detected: number;
  scans_today: number;
  avg_risk_score: number;
  urls_scanned: number;
  risk_distribution: Record<RiskLevel, number>;
}

export interface TrendPoint {
  date: string;
  scans: number;
  threats: number;
}

export interface Investigation {
  id: string;
  title: string;
  description: string | null;
  priority: "Low" | "Medium" | "High" | "Critical";
  severity: "Low" | "Medium" | "High" | "Critical";
  status: "Open" | "In Progress" | "Escalated" | "Closed";
  created_at: string;
  updated_at: string;
}

export interface InvestigationDetail extends Investigation {
  artifacts: { id: string; artifact_type: string; artifact_value: string; added_at: string }[];
  notes: { id: string; content: string; created_at: string; author_id: string }[];
  timeline: { id: string; event_type: string; description: string; timestamp: string }[];
}

export interface SearchItem {
  id: string;
  type: "ioc" | "scan";
  value: string;
  classification: string | null;
  risk_level: string | null;
  first_seen?: string | null;
}

export interface IocDetail {
  value: string;
  ioc_type: string;
  threat_score: number;
  first_seen: string;
  last_seen: string;
  timeline: { date: string; description: string }[];
  relationships: {
    related_domains: string[];
    related_ips: string[];
    related_urls: string[];
    related_senders: string[];
    related_hashes: string[];
    related_scans: string[];
    relationship_count: number;
  };
  linked_scans: { id: string; subject: string; date: string | null; risk: RiskLevel }[];
}

export interface Campaign {
  name: string;
  confidence: "Low" | "Medium" | "High";
  affected_scans_count: number;
  shared_indicators: string[];
  first_seen: string;
  last_seen: string;
  scans: { id: string; subject: string }[];
}

export interface GraphPayload {
  nodes: { id: string; label: string; type: string; degree: number }[];
  edges: { source: string; target: string; type: string; confidence: string }[];
  total_nodes?: number;
  total_edges?: number;
}

export interface Recommendation {
  id: string;
  playbook_name: string;
  recommendation_type: string;
  status: "pending" | "approved" | "rejected" | "executed" | string;
  confidence_score: number;
  confidence_level: string;
  reasoning: string;
  triggering_iocs: string[];
  affected_users_count: number;
  created_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  permissions: string[];
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface Member {
  id: string;
  user_id: string;
  role: string;
  is_active: boolean;
  joined_at: string;
  email: string | null;
  full_name: string | null;
}

export interface Invite {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  invitation_token?: string;
}

export interface Report {
  id: string;
  report_type: string;
  status: "pending" | "processing" | "completed" | "failed";
  scan_id: string | null;
  investigation_id: string | null;
  created_at: string | null;
}

export interface CopilotTurn {
  role: "user" | "assistant";
  content: string;
}
