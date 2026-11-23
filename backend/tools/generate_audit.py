import json

audit = [
    {
        "rule_name": "Business Email Compromise (BEC)",
        "trigger_conditions": [
            "High urgency language detected",
            "Financial request OR credential request context present",
            "Sender anomaly (e.g., mismatch between display name and domain)"
        ],
        "matched_patterns": ["<urgent_keyword> + <financial_keyword>", "<display_name_anomaly>"],
        "risk_contribution": 40.0,
        "mitre_mappings": ["T1586", "T1566.004"],
        "expected_false_positive_scenarios": [
            "Legitimate internal finance requests using urgent language"
        ],
        "expected_false_negative_scenarios": [
            "BEC using compromised internal accounts with no urgency language"
        ]
    },
    {
        "rule_name": "Brand Impersonation",
        "trigger_conditions": [
            "Targeted brand name mentioned in email body or subject",
            "Sender domain does not match official brand domain",
            "Sender display name implies official brand affiliation"
        ],
        "matched_patterns": ["<brand_name> + <domain_mismatch>", "<homoglyph_domain>"],
        "risk_contribution": 35.0,
        "mitre_mappings": ["T1566", "T1036"],
        "expected_false_positive_scenarios": [
            "Third-party authorized vendors emailing on behalf of the brand"
        ],
        "expected_false_negative_scenarios": [
            "Impersonation using compromised legitimate infrastructure (e.g., SendGrid without SPF/DKIM strictness)"
        ]
    },
    {
        "rule_name": "Credential Harvesting Attempt",
        "trigger_conditions": [
            "Explicit login/authentication request",
            "Credential collection intent (forms or links to external unverified domains)"
        ],
        "matched_patterns": ["<login_intent> + <external_untrusted_link>", "<password_form>"],
        "risk_contribution": 30.0,
        "mitre_mappings": ["T1566.002", "T1040"],
        "expected_false_positive_scenarios": [
            "Legitimate password reset emails from external third-party services"
        ],
        "expected_false_negative_scenarios": [
            "Credential harvesting via legitimate file sharing links (e.g., SharePoint, Google Drive)"
        ]
    },
    {
        "rule_name": "Invoice Fraud Attempt",
        "trigger_conditions": [
            "Email references unpaid invoices or remittance",
            "External link or attachment included",
            "Sender domain is not recognized as a known vendor"
        ],
        "matched_patterns": ["<invoice_keyword> + <attachment/link> + <unknown_sender>"],
        "risk_contribution": 25.0,
        "mitre_mappings": ["T1566"],
        "expected_false_positive_scenarios": [
            "Legitimate invoices from new vendors"
        ],
        "expected_false_negative_scenarios": [
            "Compromised known vendor sending fraudulent invoices"
        ]
    },
    {
        "rule_name": "Malware Delivery",
        "trigger_conditions": [
            "Suspicious file extension (e.g., .exe, .scr, .vbs, .js) OR macro-enabled document",
            "Encouragement to execute or enable content"
        ],
        "matched_patterns": ["<suspicious_extension>", "<macro_enable_intent>"],
        "risk_contribution": 45.0,
        "mitre_mappings": ["T1566.001", "T1204.002"],
        "expected_false_positive_scenarios": [
            "Legitimate sharing of scripts or tools among developers"
        ],
        "expected_false_negative_scenarios": [
            "0-day exploits in benign-looking document formats"
        ]
    },
    {
        "rule_name": "QR Code Phishing (Quishing)",
        "trigger_conditions": [
            "Image attachment or embedded image containing a QR code",
            "Call to action to scan the code for authentication or payment"
        ],
        "matched_patterns": ["<qr_image_detected> + <scan_intent>"],
        "risk_contribution": 35.0,
        "mitre_mappings": ["T1566"],
        "expected_false_positive_scenarios": [
            "Legitimate event tickets or boarding passes"
        ],
        "expected_false_negative_scenarios": [
            "Heavily obfuscated QR codes that evade image processing"
        ]
    },
    {
        "rule_name": "OAuth Consent Phishing",
        "trigger_conditions": [
            "Link pointing to known OAuth authorization endpoints (e.g., login.microsoftonline.com/oauth2)",
            "Suspicious client_id or missing verified publisher context"
        ],
        "matched_patterns": ["<oauth_endpoint> + <suspicious_client_id>"],
        "risk_contribution": 40.0,
        "mitre_mappings": ["T1528"],
        "expected_false_positive_scenarios": [
            "Legitimate internal application onboarding"
        ],
        "expected_false_negative_scenarios": [
            "Consent phishing using compromised verified publisher accounts"
        ]
    },
    {
        "rule_name": "MFA Fatigue / Push Spam",
        "trigger_conditions": [
            "Email alerts regarding multiple failed login attempts or MFA codes",
            "Instructions to approve a pending request or call a fraudulent support number"
        ],
        "matched_patterns": ["<mfa_alert> + <fraudulent_support_number/approve_intent>"],
        "risk_contribution": 35.0,
        "mitre_mappings": ["T1621"],
        "expected_false_positive_scenarios": [
            "Legitimate high-volume MFA alerts during a real attack (though this is still an incident)"
        ],
        "expected_false_negative_scenarios": [
            "MFA fatigue executed entirely via SMS/voice without email context"
        ]
    },
    {
        "rule_name": "Cryptocurrency Extortion / Scam",
        "trigger_conditions": [
            "Mention of cryptocurrency (Bitcoin, ETH, wallets)",
            "Extortion threat OR promise of high returns"
        ],
        "matched_patterns": ["<crypto_keyword> + <extortion_intent/scam_intent>"],
        "risk_contribution": 30.0,
        "mitre_mappings": ["T1498", "T1566"],
        "expected_false_positive_scenarios": [
            "Legitimate communications regarding corporate crypto investments"
        ],
        "expected_false_negative_scenarios": [
            "Scams using subtle language without explicit wallet addresses"
        ]
    },
    {
        "rule_name": "Fake Recruiting Campaign",
        "trigger_conditions": [
            "Unsolicited job offer or interview request",
            "Request for personal information, upfront payment, or clicking a suspicious link"
        ],
        "matched_patterns": ["<job_offer_intent> + <data_collection/payment_intent>"],
        "risk_contribution": 20.0,
        "mitre_mappings": ["T1566.002"],
        "expected_false_positive_scenarios": [
            "Legitimate aggressive recruiting campaigns from external headhunters"
        ],
        "expected_false_negative_scenarios": [
            "Highly targeted fake recruiting using scraped LinkedIn data for context"
        ]
    }
]

with open("detection_audit.json", "w") as f:
    json.dump(audit, f, indent=4)
print("detection_audit.json generated.")
