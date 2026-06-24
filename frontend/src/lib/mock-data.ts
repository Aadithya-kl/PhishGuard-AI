// ============================================================================
// PhishGuard AI - Comprehensive Mock Data
// ============================================================================

import type {
  DashboardStats, TrendData, RiskDistribution, AttackCategory, TopDomain,
  EmailScan, HeaderAnalysis, URLAnalysis, AttachmentAnalysis, AIAnalysis,
  Evidence, GraphData, ThreatCampaign, CopilotResponse, Report,
  Notification, AuditLogEntry, User
} from '@/types';

// --- Dashboard Mock Data ---
export const mockDashboardStats: DashboardStats = {
  total_scans: 12847,
  threats_detected: 3291,
  avg_risk_score: 34.7,
  scans_today: 147,
  high_risk_count: 892,
  campaigns_active: 7,
};

export const mockTrendData: TrendData[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  const total = Math.floor(Math.random() * 200) + 300;
  const high_risk = Math.floor(total * (0.05 + Math.random() * 0.15));
  const suspicious = Math.floor(total * (0.1 + Math.random() * 0.15));
  const safe = total - high_risk - suspicious;
  return {
    date: date.toISOString().split('T')[0],
    total,
    high_risk,
    suspicious,
    safe,
  };
});

export const mockRiskDistribution: RiskDistribution = {
  safe: 6420,
  low: 2890,
  suspicious: 2145,
  high: 1392,
};

export const mockAttackCategories: AttackCategory[] = [
  { category: 'Credential Phishing', count: 1247, percentage: 37.9 },
  { category: 'BEC / Impersonation', count: 832, percentage: 25.3 },
  { category: 'Malware Delivery', count: 521, percentage: 15.8 },
  { category: 'Spear Phishing', count: 389, percentage: 11.8 },
  { category: 'Invoice Fraud', count: 187, percentage: 5.7 },
  { category: 'Brand Spoofing', count: 115, percentage: 3.5 },
];

export const mockTopDomains: TopDomain[] = [
  { domain: 'secure-login-microsoft.com', scan_count: 234, avg_risk: 92.3, last_seen: '2026-06-16T10:23:00Z' },
  { domain: 'paypa1-verify.net', scan_count: 187, avg_risk: 89.7, last_seen: '2026-06-16T09:45:00Z' },
  { domain: 'docusign-review.xyz', scan_count: 156, avg_risk: 85.2, last_seen: '2026-06-16T08:12:00Z' },
  { domain: 'amaz0n-security.com', scan_count: 143, avg_risk: 87.1, last_seen: '2026-06-15T22:30:00Z' },
  { domain: 'wells-fargo-alert.info', scan_count: 98, avg_risk: 83.6, last_seen: '2026-06-15T18:45:00Z' },
  { domain: 'apple-id-suspended.com', scan_count: 87, avg_risk: 91.4, last_seen: '2026-06-15T14:20:00Z' },
  { domain: 'chase-secure-login.net', scan_count: 76, avg_risk: 79.8, last_seen: '2026-06-14T23:10:00Z' },
  { domain: 'dropbox-share.click', scan_count: 65, avg_risk: 72.4, last_seen: '2026-06-14T16:55:00Z' },
];

// --- Evidence Helpers ---
const headerEvidence: Evidence[] = [
  { type: 'header', description: 'SPF record check failed - sender IP not authorized for domain', severity: 'high', impact_on_score: 25 },
  { type: 'header', description: 'DKIM signature verification failed - message integrity compromised', severity: 'high', impact_on_score: 20 },
  { type: 'header', description: 'Display name impersonation detected: "Microsoft Security" from non-Microsoft domain', severity: 'critical', impact_on_score: 30 },
  { type: 'header', description: 'Reply-To address differs from sender address', severity: 'medium', impact_on_score: 10 },
];

const urlEvidence: Evidence[] = [
  { type: 'url', description: 'Domain registered 2 days ago - newly registered domain', severity: 'high', impact_on_score: 20 },
  { type: 'url', description: 'URL uses homoglyph substitution: "rnicrosoft.com" mimics "microsoft.com"', severity: 'critical', impact_on_score: 30 },
  { type: 'url', description: 'Multiple redirects through URL shortener services detected', severity: 'medium', impact_on_score: 15 },
  { type: 'url', description: 'Final landing page hosts a credential harvesting form', severity: 'critical', impact_on_score: 35 },
];

const attachmentEvidence: Evidence[] = [
  { type: 'attachment', description: 'File contains VBA macros with auto-execute functionality', severity: 'critical', impact_on_score: 35 },
  { type: 'attachment', description: 'Double file extension detected: invoice.pdf.exe', severity: 'high', impact_on_score: 25 },
];

const aiEvidence: Evidence[] = [
  { type: 'ai', description: 'Language analysis indicates urgency manipulation tactics', severity: 'high', impact_on_score: 15 },
  { type: 'ai', description: 'Email pattern matches known credential phishing campaign templates', severity: 'high', impact_on_score: 20 },
  { type: 'ai', description: 'Sender behavior anomaly: first email from this address to recipient', severity: 'medium', impact_on_score: 10 },
];

// --- Scan Mock Data ---
const mockHeaderAnalysis: HeaderAnalysis = {
  id: 'ha-001',
  spf_pass: false,
  spf_result: 'fail',
  dkim_pass: false,
  dkim_result: 'fail',
  dmarc_pass: false,
  dmarc_result: 'fail',
  sender_spoofed: true,
  display_name_impersonation: true,
  domain_mismatch: true,
  relay_chain: [
    { hop: 1, from_server: 'mail-out.attacker.com', by_server: 'mx1.gateway.com', timestamp: '2026-06-16T10:00:01Z', protocol: 'ESMTP', delay_seconds: 0 },
    { hop: 2, from_server: 'mx1.gateway.com', by_server: 'mx2.relay.net', timestamp: '2026-06-16T10:00:03Z', protocol: 'ESMTPS', delay_seconds: 2 },
    { hop: 3, from_server: 'mx2.relay.net', by_server: 'mail.target.com', timestamp: '2026-06-16T10:00:05Z', protocol: 'ESMTPS', delay_seconds: 2 },
  ],
  forged_headers: [
    { header: 'From', expected: 'attacker@malicious.com', actual: 'security@microsoft.com', description: 'From header domain does not match authenticated sender' },
  ],
  bec_indicators: [
    { type: 'executive_impersonation', description: 'Display name matches known executive pattern', confidence: 0.87 },
    { type: 'urgency_language', description: 'Subject contains urgent action request', confidence: 0.92 },
  ],
  trust_score: 12,
  evidence: headerEvidence,
};

const mockURLAnalyses: URLAnalysis[] = [
  {
    id: 'url-001',
    original_url: 'https://bit.ly/3xK9mN2',
    final_url: 'https://secure-login-rnicrosoft.com/auth/login',
    domain: 'secure-login-rnicrosoft.com',
    domain_age_days: 2,
    registrar: 'NameCheap Inc.',
    whois_data: { registrant: 'REDACTED FOR PRIVACY', country: 'RU', nameservers: ['ns1.shadydns.com', 'ns2.shadydns.com'] },
    redirect_chain: [
      { url: 'https://bit.ly/3xK9mN2', status_code: 301, server: 'bit.ly' },
      { url: 'https://t.co/redirect123', status_code: 302, server: 'Twitter' },
      { url: 'https://secure-login-rnicrosoft.com/auth/login', status_code: 200, server: 'nginx' },
    ],
    is_shortened: true,
    is_homoglyph: true,
    is_typosquatting: true,
    is_ip_based: false,
    tld: 'com',
    risk_score: 95,
    threat_intel_results: { virustotal: { malicious: 12, suspicious: 5, clean: 45 }, safebrowsing: { threat: 'SOCIAL_ENGINEERING' } },
    evidence: urlEvidence,
  },
  {
    id: 'url-002',
    original_url: 'https://tracking.legit-marketing.com/click?id=abc123',
    final_url: 'https://tracking.legit-marketing.com/click?id=abc123',
    domain: 'legit-marketing.com',
    domain_age_days: 1825,
    registrar: 'GoDaddy',
    whois_data: { registrant: 'Marketing Corp', country: 'US' },
    redirect_chain: [],
    is_shortened: false,
    is_homoglyph: false,
    is_typosquatting: false,
    is_ip_based: false,
    tld: 'com',
    risk_score: 15,
    threat_intel_results: { virustotal: { malicious: 0, suspicious: 0, clean: 62 } },
    evidence: [{ type: 'url', description: 'URL appears to be a legitimate marketing tracker', severity: 'info', impact_on_score: 0 }],
  },
];

const mockAttachmentAnalyses: AttachmentAnalysis[] = [
  {
    id: 'att-001',
    filename: 'Invoice_June2026.pdf.exe',
    content_type: 'application/x-msdownload',
    file_size: 245760,
    md5_hash: 'a1b2c3d4e5f6789012345678abcdef01',
    sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    is_executable: true,
    has_macros: false,
    is_double_extension: true,
    file_metadata: { packer: 'UPX', compilation_timestamp: '2026-06-14T08:00:00Z', imports: ['ws2_32.dll', 'crypt32.dll'] },
    threat_score: 95,
    evidence: attachmentEvidence,
  },
];

const mockAIAnalysis: AIAnalysis = {
  id: 'ai-001',
  model_used: 'PhishGuard-LLM v3.2 (GPT-4 Turbo)',
  attack_classification: 'Credential Phishing',
  confidence_score: 0.96,
  severity_level: 'critical',
  reasoning: `This email exhibits multiple high-confidence indicators of a credential phishing attack:

1. **Sender Impersonation**: The display name "Microsoft Security Team" is used with a non-Microsoft sending domain, indicating deliberate impersonation.

2. **Urgency Manipulation**: The subject line "URGENT: Your account has been compromised" creates artificial urgency to bypass the recipient's critical thinking.

3. **Malicious URL**: The primary link uses homoglyph substitution (rn→m) to mimic microsoft.com, passes through multiple redirectors, and lands on a newly registered domain hosting a credential harvesting form.

4. **Social Engineering**: The email body uses fear-based tactics, threatening account suspension if action is not taken within 24 hours.

5. **Technical Deception**: Multiple email authentication mechanisms (SPF, DKIM, DMARC) all fail, indicating the sender is not authorized to send on behalf of the claimed domain.`,
  tactics_detected: [
    { tactic: 'Credential Harvesting', description: 'Landing page mimics Microsoft login portal to steal credentials', confidence: 0.97, evidence: 'Login form fields match Microsoft 365 authentication page layout' },
    { tactic: 'Domain Impersonation', description: 'Homoglyph attack using "rn" to mimic "m" in microsoft.com', confidence: 0.99, evidence: 'Domain analysis confirms character substitution pattern' },
    { tactic: 'Urgency Creation', description: 'Time-limited threat to force immediate action', confidence: 0.94, evidence: '24-hour deadline mentioned in email body' },
    { tactic: 'Authority Impersonation', description: 'Poses as Microsoft Security Team', confidence: 0.95, evidence: 'Display name and email signature match Microsoft branding' },
  ],
  structured_output: {
    kill_chain_phase: 'delivery',
    target_type: 'credentials',
    brand_impersonated: 'Microsoft',
    sophistication: 'medium-high',
  },
  evidence: aiEvidence,
};

export const mockScans: EmailScan[] = [
  {
    id: 'scan-001',
    user_id: 'user-001',
    subject: 'URGENT: Your Microsoft account has been compromised',
    sender_address: 'security@secure-login-rnicrosoft.com',
    sender_display_name: 'Microsoft Security Team',
    recipient: 'john.doe@company.com',
    reply_to: 'noreply@temp-mail.xyz',
    return_path: 'bounce@secure-login-rnicrosoft.com',
    raw_headers: 'Received: from mail-out.attacker.com ...\nFrom: "Microsoft Security Team" <security@secure-login-rnicrosoft.com>\nTo: john.doe@company.com\nSubject: URGENT: Your Microsoft account has been compromised\nDate: Mon, 16 Jun 2026 10:00:00 +0000\nMessage-ID: <abc123@attacker.com>\nMIME-Version: 1.0\nContent-Type: multipart/mixed; boundary="boundary123"',
    body_text: 'Dear User,\n\nWe have detected unusual sign-in activity on your Microsoft account. Your account security is at risk.\n\nPlease verify your identity immediately by clicking the link below:\n\nhttps://bit.ly/3xK9mN2\n\nIf you do not verify within 24 hours, your account will be permanently suspended.\n\nMicrosoft Security Team',
    body_html: '<html><body style="font-family: Segoe UI, sans-serif;"><div style="max-width:600px;margin:0 auto;"><img src="https://secure-login-rnicrosoft.com/logo.png" alt="Microsoft" style="height:40px;"><h2>Account Security Alert</h2><p>Dear User,</p><p>We have detected <strong>unusual sign-in activity</strong> on your Microsoft account. Your account security is at risk.</p><p>Please verify your identity immediately:</p><a href="https://bit.ly/3xK9mN2" style="background:#0078d4;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Verify Your Account</a><p style="color:#666;font-size:12px;">If you do not verify within 24 hours, your account will be permanently suspended.</p><hr><p style="color:#999;font-size:11px;">Microsoft Corporation, One Microsoft Way, Redmond, WA 98052</p></div></body></html>',
    parsed_headers: { from: 'security@secure-login-rnicrosoft.com', to: 'john.doe@company.com' },
    mime_structure: { type: 'multipart/mixed', parts: [{ type: 'text/plain' }, { type: 'text/html' }, { type: 'application/x-msdownload', filename: 'Invoice_June2026.pdf.exe' }] },
    overall_risk_score: 94,
    risk_level: 'high',
    attack_type: 'Credential Phishing',
    risk_breakdown: { header_score: 88, url_score: 95, attachment_score: 92, ai_score: 96, overall_score: 94, risk_level: 'high' },
    investigation_report: {
      executive_summary: 'A sophisticated credential phishing campaign targeting Microsoft 365 users was detected. The attack employs homoglyph domain impersonation, URL shortener obfuscation, and social engineering urgency tactics. The attached executable disguised as a PDF poses additional malware risk. Immediate blocking of the sender domain and user notification is recommended.',
      detailed_findings: [
        { category: 'Email Authentication', title: 'Complete Authentication Failure', description: 'All email authentication mechanisms (SPF, DKIM, DMARC) failed', severity: 'critical', evidence: ['SPF: fail', 'DKIM: fail', 'DMARC: fail'] },
        { category: 'URL Analysis', title: 'Homoglyph Domain Attack', description: 'Primary URL uses character substitution to mimic microsoft.com', severity: 'critical', evidence: ['Domain: secure-login-rnicrosoft.com', 'Age: 2 days', 'Registrar: NameCheap'] },
        { category: 'Attachment', title: 'Disguised Executable', description: 'Attachment uses double extension to appear as PDF', severity: 'critical', evidence: ['Filename: Invoice_June2026.pdf.exe', 'True type: PE executable'] },
      ],
      attack_chain: [
        { id: 'ac-1', type: 'sender', label: 'Attacker', description: 'Sends spoofed email', risk_level: 'high' },
        { id: 'ac-2', type: 'email', label: 'Phishing Email', description: 'Impersonates Microsoft', risk_level: 'high' },
        { id: 'ac-3', type: 'url', label: 'Shortened URL', description: 'bit.ly redirect', risk_level: 'medium' },
        { id: 'ac-4', type: 'redirect', label: 'Multi-hop Redirect', description: 'Through t.co', risk_level: 'medium' },
        { id: 'ac-5', type: 'landing', label: 'Fake Login Page', description: 'Credential harvester', risk_level: 'critical' },
        { id: 'ac-6', type: 'objective', label: 'Credential Theft', description: 'Steal M365 credentials', risk_level: 'critical' },
      ],
      threat_actor_profile: { name: 'Storm-0539 Variant', type: 'Cybercrime', sophistication: 'Medium-High', known_campaigns: ['Microsoft 365 Phishing Wave Q2 2026'], ttps: ['T1566.001 - Spearphishing Attachment', 'T1204 - User Execution', 'T1078 - Valid Accounts'] },
      mitigation_actions: [
        'Block sender domain: secure-login-rnicrosoft.com',
        'Block IP range associated with mail-out.attacker.com',
        'Notify recipient to reset credentials if link was clicked',
        'Add URL pattern to web filter blocklist',
        'Quarantine and delete the attached executable',
        'Update email gateway rules to flag homoglyph domains',
        'Conduct phishing awareness training for affected department',
      ],
      risk_assessment: { overall_risk: 'Critical', impact: 'High - Potential credential compromise', likelihood: 'High - Active campaign targeting organization', affected_systems: ['Microsoft 365', 'Email Gateway', 'User Endpoints'] },
      timeline: [
        { timestamp: '2026-06-16T09:58:00Z', event: 'Email sent from attacker infrastructure', category: 'delivery', details: 'Origin: mail-out.attacker.com' },
        { timestamp: '2026-06-16T10:00:01Z', event: 'Email received by gateway', category: 'delivery', details: 'Passed initial filters' },
        { timestamp: '2026-06-16T10:00:05Z', event: 'Email delivered to inbox', category: 'delivery', details: 'Delivered to john.doe@company.com' },
        { timestamp: '2026-06-16T10:23:00Z', event: 'PhishGuard scan initiated', category: 'detection', details: 'Automated scan triggered' },
        { timestamp: '2026-06-16T10:23:15Z', event: 'Threat detected', category: 'detection', details: 'Risk score: 94/100' },
      ],
    },
    status: 'completed',
    scanned_at: '2026-06-16T10:23:00Z',
    header_analysis: mockHeaderAnalysis,
    url_analyses: mockURLAnalyses,
    attachment_analyses: mockAttachmentAnalyses,
    ai_analysis: mockAIAnalysis,
  },
  {
    id: 'scan-002',
    user_id: 'user-001',
    subject: 'Re: Q3 Budget Approval - Wire Transfer Required',
    sender_address: 'ceo@company-mail.net',
    sender_display_name: 'David Chen (CEO)',
    recipient: 'finance@company.com',
    raw_headers: '',
    body_text: 'Hi Finance Team,\n\nI need you to process an urgent wire transfer for a confidential acquisition. Please transfer $147,000 to the following account:\n\nBank: First National\nAccount: 29384756\nRouting: 021000021\n\nThis is time-sensitive. Do not discuss with anyone else. I am in meetings all day.\n\nDavid Chen\nCEO',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 87,
    risk_level: 'high',
    attack_type: 'BEC / CEO Fraud',
    risk_breakdown: { header_score: 75, url_score: 10, attachment_score: 0, ai_score: 92, overall_score: 87, risk_level: 'high' },
    status: 'completed',
    scanned_at: '2026-06-16T09:45:00Z',
    header_analysis: { ...mockHeaderAnalysis, id: 'ha-002', spf_pass: true, spf_result: 'pass', dkim_pass: true, dkim_result: 'pass', trust_score: 45 },
    ai_analysis: { ...mockAIAnalysis, id: 'ai-002', attack_classification: 'BEC / CEO Fraud', confidence_score: 0.93, reasoning: 'Classic BEC pattern: CEO impersonation, urgent wire transfer request, secrecy instruction, unavailability claim.' },
  },
  {
    id: 'scan-003',
    user_id: 'user-001',
    subject: 'Your Amazon order #302-1234567 has shipped',
    sender_address: 'ship-confirm@amazon.com',
    sender_display_name: 'Amazon.com',
    recipient: 'jane.smith@company.com',
    raw_headers: '',
    body_text: 'Your order has shipped! Track your package at amazon.com/track/123456',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 8,
    risk_level: 'safe',
    attack_type: undefined,
    risk_breakdown: { header_score: 5, url_score: 10, attachment_score: 0, ai_score: 8, overall_score: 8, risk_level: 'safe' },
    status: 'completed',
    scanned_at: '2026-06-16T08:30:00Z',
  },
  {
    id: 'scan-004',
    user_id: 'user-001',
    subject: 'DocuSign: Please review and sign document',
    sender_address: 'noreply@docusign-review.xyz',
    sender_display_name: 'DocuSign',
    recipient: 'mark.johnson@company.com',
    raw_headers: '',
    body_text: 'Mark Johnson, please review and sign this document. Click here to review.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 72,
    risk_level: 'suspicious',
    attack_type: 'Brand Spoofing',
    risk_breakdown: { header_score: 65, url_score: 78, attachment_score: 0, ai_score: 70, overall_score: 72, risk_level: 'suspicious' },
    status: 'completed',
    scanned_at: '2026-06-16T07:15:00Z',
  },
  {
    id: 'scan-005',
    user_id: 'user-001',
    subject: 'Invoice #INV-2026-0892 - Payment Overdue',
    sender_address: 'billing@supplier-invoices.com',
    sender_display_name: 'Accounts Payable',
    recipient: 'accounts@company.com',
    raw_headers: '',
    body_text: 'Please find attached invoice for immediate payment. Bank details have been updated.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 81,
    risk_level: 'high',
    attack_type: 'Invoice Fraud',
    risk_breakdown: { header_score: 70, url_score: 45, attachment_score: 85, ai_score: 88, overall_score: 81, risk_level: 'high' },
    status: 'completed',
    scanned_at: '2026-06-15T16:40:00Z',
    attachment_analyses: [{
      id: 'att-005',
      filename: 'Invoice-0892.xlsm',
      content_type: 'application/vnd.ms-excel.sheet.macroEnabled',
      file_size: 128000,
      md5_hash: 'f1e2d3c4b5a697867564534231201f0e',
      sha256_hash: 'abc123def456789012345678901234567890abcdef1234567890abcdef12345678',
      is_executable: false,
      has_macros: true,
      is_double_extension: false,
      file_metadata: { macro_count: 3, auto_open: true },
      threat_score: 85,
      evidence: [{ type: 'attachment', description: 'Excel file contains macros with auto-execute on open', severity: 'high', impact_on_score: 25 }],
    }],
  },
  {
    id: 'scan-006',
    user_id: 'user-001',
    subject: 'Team Meeting Notes - Sprint Planning',
    sender_address: 'sarah.wilson@company.com',
    sender_display_name: 'Sarah Wilson',
    recipient: 'team@company.com',
    raw_headers: '',
    body_text: 'Hi team, here are the notes from today\'s sprint planning meeting.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 3,
    risk_level: 'safe',
    risk_breakdown: { header_score: 2, url_score: 0, attachment_score: 5, ai_score: 3, overall_score: 3, risk_level: 'safe' },
    status: 'completed',
    scanned_at: '2026-06-15T14:20:00Z',
  },
  {
    id: 'scan-007',
    user_id: 'user-001',
    subject: 'Password Reset Request - Action Required',
    sender_address: 'no-reply@paypa1-verify.net',
    sender_display_name: 'PayPal Security',
    recipient: 'alex.brown@company.com',
    raw_headers: '',
    body_text: 'We noticed suspicious activity on your PayPal account. Reset your password now.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 89,
    risk_level: 'high',
    attack_type: 'Credential Phishing',
    risk_breakdown: { header_score: 82, url_score: 91, attachment_score: 0, ai_score: 90, overall_score: 89, risk_level: 'high' },
    status: 'completed',
    scanned_at: '2026-06-15T11:30:00Z',
  },
  {
    id: 'scan-008',
    user_id: 'user-001',
    subject: 'Quarterly Report - Financials Attached',
    sender_address: 'reports@company.com',
    sender_display_name: 'Automated Reports',
    recipient: 'management@company.com',
    raw_headers: '',
    body_text: 'Please find the Q2 2026 financial report attached.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 5,
    risk_level: 'safe',
    risk_breakdown: { header_score: 3, url_score: 0, attachment_score: 8, ai_score: 4, overall_score: 5, risk_level: 'safe' },
    status: 'completed',
    scanned_at: '2026-06-15T09:00:00Z',
  },
  {
    id: 'scan-009',
    user_id: 'user-001',
    subject: 'Shared Document: Project Proposal',
    sender_address: 'noreply@dropbox-share.click',
    sender_display_name: 'Dropbox',
    recipient: 'lisa.chen@company.com',
    raw_headers: '',
    body_text: 'A document has been shared with you. Click to view.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 67,
    risk_level: 'suspicious',
    attack_type: 'Brand Spoofing',
    risk_breakdown: { header_score: 60, url_score: 72, attachment_score: 0, ai_score: 65, overall_score: 67, risk_level: 'suspicious' },
    status: 'completed',
    scanned_at: '2026-06-14T22:15:00Z',
  },
  {
    id: 'scan-010',
    user_id: 'user-001',
    subject: 'IT Support: System Update Required',
    sender_address: 'it-support@company-helpdesk.com',
    sender_display_name: 'IT Support',
    recipient: 'all-staff@company.com',
    raw_headers: '',
    body_text: 'Please install the attached system update to ensure security compliance.',
    body_html: '',
    parsed_headers: {},
    mime_structure: {},
    overall_risk_score: 45,
    risk_level: 'suspicious',
    attack_type: 'Spear Phishing',
    risk_breakdown: { header_score: 40, url_score: 30, attachment_score: 55, ai_score: 48, overall_score: 45, risk_level: 'suspicious' },
    status: 'completed',
    scanned_at: '2026-06-14T18:00:00Z',
  },
];

// --- Knowledge Graph Mock Data ---
export const mockGraphData: GraphData = {
  nodes: [
    { id: 'n1', type: 'sender', label: 'security@secure-login-rnicrosoft.com', properties: { display_name: 'Microsoft Security Team' }, risk_score: 94 },
    { id: 'n2', type: 'domain', label: 'secure-login-rnicrosoft.com', properties: { registrar: 'NameCheap', age_days: 2 }, risk_score: 95 },
    { id: 'n3', type: 'email', label: 'URGENT: Account compromised', properties: { subject: 'URGENT: Your Microsoft account has been compromised' }, risk_score: 94 },
    { id: 'n4', type: 'url', label: 'bit.ly/3xK9mN2', properties: { is_shortened: true }, risk_score: 85 },
    { id: 'n5', type: 'url', label: 'secure-login-rnicrosoft.com/auth', properties: { is_homoglyph: true }, risk_score: 95 },
    { id: 'n6', type: 'ip', label: '185.234.72.19', properties: { country: 'RU', asn: 'AS12345' }, risk_score: 88 },
    { id: 'n7', type: 'campaign', label: 'MS365 Phishing Wave', properties: { attack_type: 'Credential Phishing' }, risk_score: 92 },
    { id: 'n8', type: 'sender', label: 'ceo@company-mail.net', properties: { display_name: 'David Chen (CEO)' }, risk_score: 87 },
    { id: 'n9', type: 'email', label: 'Wire Transfer Required', properties: { subject: 'Re: Q3 Budget Approval' }, risk_score: 87 },
    { id: 'n10', type: 'domain', label: 'company-mail.net', properties: { registrar: 'GoDaddy', age_days: 14 }, risk_score: 72 },
    { id: 'n11', type: 'sender', label: 'no-reply@paypa1-verify.net', properties: { display_name: 'PayPal Security' }, risk_score: 89 },
    { id: 'n12', type: 'domain', label: 'paypa1-verify.net', properties: { registrar: 'Tucows', age_days: 5 }, risk_score: 91 },
    { id: 'n13', type: 'email', label: 'Password Reset Request', properties: { subject: 'Password Reset Request' }, risk_score: 89 },
    { id: 'n14', type: 'ip', label: '91.215.85.42', properties: { country: 'UA', asn: 'AS67890' }, risk_score: 82 },
    { id: 'n15', type: 'campaign', label: 'PayPal Credential Harvest', properties: { attack_type: 'Credential Phishing' }, risk_score: 89 },
    { id: 'n16', type: 'domain', label: 'docusign-review.xyz', properties: { registrar: 'NameSilo', age_days: 7 }, risk_score: 78 },
    { id: 'n17', type: 'sender', label: 'noreply@docusign-review.xyz', properties: { display_name: 'DocuSign' }, risk_score: 72 },
  ],
  edges: [
    { id: 'e1', source: 'n1', target: 'n3', relationship: 'SENT', properties: {} },
    { id: 'e2', source: 'n1', target: 'n2', relationship: 'USES_DOMAIN', properties: {} },
    { id: 'e3', source: 'n3', target: 'n4', relationship: 'CONTAINS_URL', properties: {} },
    { id: 'e4', source: 'n4', target: 'n5', relationship: 'REDIRECTS_TO', properties: {} },
    { id: 'e5', source: 'n5', target: 'n2', relationship: 'HOSTED_ON', properties: {} },
    { id: 'e6', source: 'n2', target: 'n6', relationship: 'RESOLVES_TO', properties: {} },
    { id: 'e7', source: 'n3', target: 'n7', relationship: 'PART_OF', properties: {} },
    { id: 'e8', source: 'n8', target: 'n9', relationship: 'SENT', properties: {} },
    { id: 'e9', source: 'n8', target: 'n10', relationship: 'USES_DOMAIN', properties: {} },
    { id: 'e10', source: 'n11', target: 'n13', relationship: 'SENT', properties: {} },
    { id: 'e11', source: 'n11', target: 'n12', relationship: 'USES_DOMAIN', properties: {} },
    { id: 'e12', source: 'n12', target: 'n14', relationship: 'RESOLVES_TO', properties: {} },
    { id: 'e13', source: 'n13', target: 'n15', relationship: 'PART_OF', properties: {} },
    { id: 'e14', source: 'n6', target: 'n14', relationship: 'SAME_NETWORK', properties: {} },
    { id: 'e15', source: 'n7', target: 'n15', relationship: 'RELATED_CAMPAIGN', properties: {} },
    { id: 'e16', source: 'n17', target: 'n16', relationship: 'USES_DOMAIN', properties: {} },
    { id: 'e17', source: 'n16', target: 'n6', relationship: 'RESOLVES_TO', properties: {} },
  ],
};

// --- Campaign Mock Data ---
export const mockCampaigns: ThreatCampaign[] = [
  {
    id: 'camp-001', name: 'Microsoft 365 Credential Harvest', description: 'Ongoing phishing campaign targeting Microsoft 365 users with homoglyph domains and credential harvesting pages.',
    attack_type: 'Credential Phishing', first_seen: '2026-05-28T00:00:00Z', last_seen: '2026-06-16T10:23:00Z', scan_count: 234,
    indicators: { domains: ['secure-login-rnicrosoft.com', 'rnicrosoftonline-auth.com'], ips: ['185.234.72.19', '185.234.72.20'], sender_addresses: ['security@secure-login-rnicrosoft.com'], subject_patterns: ['*account*compromised*', '*verify*identity*'] },
    severity: 'critical', status: 'active',
  },
  {
    id: 'camp-002', name: 'CEO Wire Transfer BEC', description: 'Business email compromise campaign impersonating C-level executives to request urgent wire transfers.',
    attack_type: 'BEC / CEO Fraud', first_seen: '2026-06-01T00:00:00Z', last_seen: '2026-06-16T09:45:00Z', scan_count: 47,
    indicators: { domains: ['company-mail.net', 'company-exec.com'], ips: ['91.215.85.42'], sender_addresses: ['ceo@company-mail.net'], subject_patterns: ['*wire transfer*', '*urgent*payment*'] },
    severity: 'high', status: 'active',
  },
  {
    id: 'camp-003', name: 'PayPal Credential Phishing Wave', description: 'Mass credential phishing using PayPal brand impersonation.',
    attack_type: 'Credential Phishing', first_seen: '2026-06-05T00:00:00Z', last_seen: '2026-06-15T11:30:00Z', scan_count: 187,
    indicators: { domains: ['paypa1-verify.net', 'paypa1-secure.com'], ips: ['91.215.85.42', '91.215.85.43'], sender_addresses: ['no-reply@paypa1-verify.net'], subject_patterns: ['*password reset*', '*suspicious activity*'] },
    severity: 'high', status: 'active',
  },
  {
    id: 'camp-004', name: 'DocuSign Brand Spoofing', description: 'Brand spoofing campaign using fake DocuSign notifications.',
    attack_type: 'Brand Spoofing', first_seen: '2026-06-10T00:00:00Z', last_seen: '2026-06-16T07:15:00Z', scan_count: 156,
    indicators: { domains: ['docusign-review.xyz', 'docusign-verify.click'], ips: ['185.234.72.19'], sender_addresses: ['noreply@docusign-review.xyz'], subject_patterns: ['*review and sign*', '*document shared*'] },
    severity: 'medium', status: 'active',
  },
  {
    id: 'camp-005', name: 'Invoice Macro Malware', description: 'Malware distribution via macro-enabled Excel invoices.',
    attack_type: 'Malware Delivery', first_seen: '2026-05-15T00:00:00Z', last_seen: '2026-06-15T16:40:00Z', scan_count: 89,
    indicators: { domains: ['supplier-invoices.com'], ips: ['203.0.113.50'], sender_addresses: ['billing@supplier-invoices.com'], subject_patterns: ['*invoice*payment*', '*overdue*'] },
    severity: 'high', status: 'active',
  },
];

// --- Report Mock Data ---
export const mockReports: Report[] = [
  {
    id: 'rpt-1',
    target_id: 'scan-1',
    report_type: 'scan',
    format: 'pdf',
    status: 'completed',
    generated_at: '2026-06-20T10:00:00Z',
    download_url: '/api/v1/reports/rpt-1/download',
  },
  {
    id: 'rpt-2',
    target_id: 'inv-1',
    report_type: 'investigation',
    format: 'pdf',
    status: 'completed',
    generated_at: '2026-06-19T14:30:00Z',
    download_url: '/api/v1/reports/rpt-2/download',
  },
  {
    id: 'rpt-3',
    target_id: 'campaign-1',
    report_type: 'campaign',
    format: 'json',
    status: 'completed',
    generated_at: '2026-06-18T09:15:00Z',
    download_url: '/api/v1/reports/rpt-3/download',
  },
];

// --- Copilot Mock Responses ---
export const mockCopilotResponses: Record<string, CopilotResponse> = {
  default: {
    message: "I'm PhishGuard AI Copilot. I can help you analyze email threats, investigate suspicious patterns, and provide security recommendations. What would you like to know?",
    suggestions: ['Analyze the latest high-risk scan', 'Show me active campaigns', 'What are the top threats today?', 'Explain the risk score breakdown'],
  },
  threat: {
    message: "Based on my analysis, this email shows strong indicators of a credential phishing attack. The sender domain uses homoglyph substitution (rn→m) to impersonate Microsoft. The URL passes through multiple redirectors before landing on a newly registered domain hosting a credential harvesting form. I recommend immediate blocking of the sender domain and notifying the recipient.",
    suggestions: ['What specific TTPs are used?', 'Are there related campaigns?', 'Generate an incident report', 'What mitigation steps should we take?'],
  },
};

// --- Notification Mock Data ---
export const mockNotifications: Notification[] = [
  { id: 'notif-001', type: 'threat', title: 'Critical Threat Detected', message: 'High-risk credential phishing email targeting john.doe@company.com', read: false, timestamp: '2026-06-16T10:23:00Z', link: '/scan/scan-001' },
  { id: 'notif-002', type: 'campaign', title: 'New Campaign Identified', message: 'Microsoft 365 credential harvesting campaign detected across 234 emails', read: false, timestamp: '2026-06-16T09:00:00Z', link: '/threat-hunting' },
  { id: 'notif-003', type: 'scan', title: 'BEC Attempt Blocked', message: 'CEO impersonation wire transfer request intercepted', read: true, timestamp: '2026-06-16T08:45:00Z', link: '/scan/scan-002' },
  { id: 'notif-004', type: 'system', title: 'System Update', message: 'PhishGuard AI models updated to v3.2', read: true, timestamp: '2026-06-15T22:00:00Z' },
];

// --- Audit Log Mock Data ---
export const mockAuditLog: AuditLogEntry[] = [
  { id: 'al-001', user_id: 'user-001', user_email: 'admin@company.com', action: 'scan.create', resource: 'scan-001', details: 'Email scan initiated', ip_address: '10.0.1.50', timestamp: '2026-06-16T10:23:00Z' },
  { id: 'al-002', user_id: 'user-001', user_email: 'admin@company.com', action: 'report.generate', resource: 'rpt-001', details: 'Executive report generated', ip_address: '10.0.1.50', timestamp: '2026-06-16T10:30:00Z' },
  { id: 'al-003', user_id: 'user-002', user_email: 'analyst@company.com', action: 'scan.view', resource: 'scan-001', details: 'Viewed scan results', ip_address: '10.0.1.51', timestamp: '2026-06-16T10:35:00Z' },
  { id: 'al-004', user_id: 'user-001', user_email: 'admin@company.com', action: 'api_key.create', resource: 'key-001', details: 'API key created: Production Key', ip_address: '10.0.1.50', timestamp: '2026-06-16T08:00:00Z' },
];

// --- Mock User ---
export const mockUser: User = {
  id: 'user-001',
  email: 'admin@company.com',
  full_name: 'Alex Morgan',
  role: 'admin',
};
