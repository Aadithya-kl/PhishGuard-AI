// ============================================================================
// PhishGuard AI - Type Definitions
// ============================================================================

// --- Core Auth Types ---
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'analyst' | 'viewer';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used?: string;
  is_active: boolean;
}

// --- Evidence & Analysis Types ---
export interface Evidence {
  type: string;
  description: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  impact_on_score: number;
}

export interface HeaderAnalysis {
  id: string;
  spf_pass?: boolean;
  spf_result: string;
  dkim_pass?: boolean;
  dkim_result: string;
  dmarc_pass?: boolean;
  dmarc_result: string;
  sender_spoofed: boolean;
  display_name_impersonation: boolean;
  domain_mismatch: boolean;
  relay_chain: RelayHop[];
  forged_headers: ForgedHeader[];
  bec_indicators: BecIndicator[];
  trust_score: number;
  evidence: Evidence[];
}

export interface RelayHop {
  hop: number;
  from_server: string;
  by_server: string;
  timestamp: string;
  protocol: string;
  delay_seconds?: number;
}

export interface ForgedHeader {
  header: string;
  expected: string;
  actual: string;
  description: string;
}

export interface BecIndicator {
  type: string;
  description: string;
  confidence: number;
}

export interface URLAnalysis {
  id: string;
  original_url: string;
  final_url?: string;
  domain: string;
  domain_age_days?: number;
  registrar?: string;
  whois_data: Record<string, any>;
  redirect_chain: RedirectHop[];
  is_shortened: boolean;
  is_homoglyph: boolean;
  is_typosquatting: boolean;
  is_ip_based: boolean;
  tld: string;
  risk_score: number;
  threat_intel_results: Record<string, any>;
  evidence: Evidence[];
}

export interface RedirectHop {
  url: string;
  status_code: number;
  server?: string;
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
  file_metadata: Record<string, any>;
  threat_score: number;
  evidence: Evidence[];
}

export interface TacticDetected {
  tactic: string;
  description: string;
  confidence: number;
  evidence: string;
}

export interface AIAnalysis {
  id: string;
  model_used: string;
  attack_classification: string;
  confidence_score: number;
  severity_level: 'low' | 'medium' | 'high' | 'critical';
  reasoning: string;
  tactics_detected: TacticDetected[];
  structured_output: Record<string, any>;
  evidence: Evidence[];
}

export interface RiskBreakdown {
  header_score: number;
  url_score: number;
  attachment_score: number;
  ai_score: number;
  overall_score: number;
  risk_level: string;
}

export interface AttackChainNode {
  id: string;
  type: string;
  label: string;
  description: string;
  risk_level: string;
}

export interface InvestigationReport {
  executive_summary: string;
  detailed_findings: DetailedFinding[];
  attack_chain: AttackChainNode[];
  threat_actor_profile?: ThreatActorProfile;
  mitigation_actions: string[];
  risk_assessment: RiskAssessment;
  timeline: TimelineEvent[];
}

export interface DetailedFinding {
  category: string;
  title: string;
  description: string;
  severity: string;
  evidence: string[];
}

export interface ThreatActorProfile {
  name?: string;
  type: string;
  sophistication: string;
  known_campaigns: string[];
  ttps: string[];
}

export interface RiskAssessment {
  overall_risk: string;
  impact: string;
  likelihood: string;
  affected_systems: string[];
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  category: string;
  details: string;
}

// --- Scan Types ---
export interface EmailScan {
  id: string;
  user_id: string;
  subject: string;
  sender_address: string;
  sender_display_name: string;
  recipient: string;
  reply_to?: string;
  return_path?: string;
  raw_headers: string;
  body_text: string;
  body_html: string;
  parsed_headers: Record<string, any>;
  mime_structure: Record<string, any>;
  overall_risk_score: number;
  risk_level: 'safe' | 'low' | 'suspicious' | 'high';
  attack_type?: string;
  risk_breakdown: RiskBreakdown;
  investigation_report?: InvestigationReport;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  scanned_at: string;
  header_analysis?: HeaderAnalysis;
  url_analyses?: URLAnalysis[];
  attachment_analyses?: AttachmentAnalysis[];
  ai_analysis?: AIAnalysis;
}

export interface ScanProgress {
  scan_id: string;
  step: string;
  progress: number;
  message: string;
  completed: boolean;
}

// --- Dashboard Types ---
export interface DashboardStats {
  total_scans: number;
  threats_detected: number;
  avg_risk_score: number;
  scans_today: number;
  high_risk_count: number;
  campaigns_active: number;
}

export interface TrendData {
  date: string;
  total: number;
  high_risk: number;
  suspicious: number;
  safe: number;
}

export interface RiskDistribution {
  safe: number;
  low: number;
  suspicious: number;
  high: number;
}

export interface AttackCategory {
  category: string;
  count: number;
  percentage: number;
}

export interface TopDomain {
  domain: string;
  scan_count: number;
  avg_risk: number;
  last_seen: string;
}

// --- Knowledge Graph Types ---
export interface GraphNode {
  id: string;
  type: string;
  label: string;
  properties: Record<string, any>;
  risk_score?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// --- Copilot Types ---
export interface CopilotMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface CopilotResponse {
  message: string;
  suggestions: string[];
  tools_used?: string[];
  sources?: string[];
  confidence?: number;
}

// --- Campaign Types ---
export interface ThreatCampaign {
  id: string;
  name: string;
  description: string;
  attack_type: string;
  first_seen: string;
  last_seen: string;
  scan_count: number;
  indicators: CampaignIndicators;
  severity: string;
  status: string;
}

export interface CampaignIndicators {
  domains: string[];
  ips: string[];
  sender_addresses: string[];
  subject_patterns: string[];
}

// --- Report Types ---
export interface Report {
  id: string;
  target_id: string;
  report_type: 'scan' | 'investigation' | 'campaign' | 'threat_actor' | 'executive';
  format: 'pdf' | 'json' | 'html';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  generated_at: string;
  download_url: string;
}

// --- Search / Threat Hunting Types ---
export interface SearchQuery {
  query: string;
  filters?: SearchFilters;
}

export interface SearchFilters {
  sender?: string;
  domain?: string;
  risk_level?: string;
  attack_type?: string;
  date_from?: string;
  date_to?: string;
}

export interface SearchResult {
  scans: EmailScan[];
  total: number;
  page: number;
  per_page: number;
}

// --- Settings Types ---
export interface IntegrationConfig {
  virustotal_api_key?: string;
  safebrowsing_api_key?: string;
  abuseipdb_api_key?: string;
  shodan_api_key?: string;
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource: string;
  details: string;
  ip_address: string;
  timestamp: string;
}

// --- Notification Types ---
export interface Notification {
  id: string;
  type: 'threat' | 'scan' | 'system' | 'campaign';
  title: string;
  message: string;
  read: boolean;
  timestamp: string;
  link?: string;
}
