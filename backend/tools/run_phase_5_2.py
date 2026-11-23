import requests
import time
import json
import uuid
import os

BASE_URL = "http://localhost:8000/api/v1"

# 10 Phishing Samples
phishing_samples = [
    # 1. Credential Harvesting
    ("Credential Harvesting", """Subject: Action Required: Verify Your Account
From: support@paypal-security-team.net
To: victim@company.com

Dear User,
Please verify your account immediately. Login to continue using your services.
<form action="http://malicious.com/login" method="POST">
  <input type="password" name="password" />
  <input type="submit" value="Verify" />
</form>"""),

    # 2. BEC
    ("Business Email Compromise", """Subject: URGENT: Wire Transfer Instructions
From: ceo@company.com
To: cfo@company.com

Are you at your desk? I need a favor. Please process an urgent wire transfer for the new acquisition.
I will send the payment instructions shortly. Immediate action required."""),

    # 3. Invoice Fraud
    ("Invoice Fraud", """Subject: OVERDUE INVOICE #99281
From: billing@vendor-services.com
To: accounts_payable@company.com

Please find the unpaid invoice attached. This is overdue and requires immediate payment to avoid service disruption.
See the remittance advice for wire details."""),

    # 4. Malware Delivery
    ("Malware Delivery", """Subject: Q3 Financial Report
From: hr@company.com
To: all-employees@company.com

The Q3 report is attached. Please review the .exe file for interactive charts.
Also, the macro-enabled .vbs script needs to be run to update your payroll details."""),

    # 5. QR Phishing
    ("QR Phishing", """Subject: MFA Update Required
From: it-admin@company.com
To: employee@company.com

We are updating our MFA policies. Please scan the QR code attached to re-authenticate your device.
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" alt="Scan the QR Code" />"""),

    # 6. OAuth Consent
    ("OAuth Consent", """Subject: Connect to New HR App
From: integrations@cloud-apps.net
To: user@company.com

The new HR portal needs permission to access your profile. Please click here to authorize app and grant access to your Microsoft 365 account."""),

    # 7. MFA Fatigue
    ("MFA Fatigue", """Subject: Unusual sign-in activity
From: security@microsoft.com
To: user@company.com

We detected an unusual sign-in. If this was you, please approve the request on your Microsoft Authenticator app.
If you do not approve sign-in, your account will be locked."""),

    # 8. Crypto Scam
    ("Cryptocurrency Scam", """Subject: You have been HACKED
From: hacker@darkweb.org
To: victim@company.com

I have recorded you using your webcam. If you don't want this sent to your contacts, send 0.5 bitcoin to my crypto wallet immediately.
Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"""),

    # 9. Fake Recruiting
    ("Fake Recruiting", """Subject: Job Offer: Remote Position
From: recruiter@fake-jobs.com
To: candidate@gmail.com

We have a remote position available for you. Work from home with a $150k salary.
Kindly message us on WhatsApp or Telegram to proceed with the background check and advance fee."""),

    # 10. Brand Impersonation
    ("Brand Impersonation", """Subject: Your Microsoft 365 Password Expires Today
From: Microsoft Support <admin@m1cr0s0ft-update.com>
To: user@company.com

Your password expires today. Please click the link to retain your current password.
Thank you,
Microsoft Security Team""")
]

# 10 Benign Samples
benign_samples = [
    ("Benign Newsletter 1", "Subject: Weekly Tech Digest\\nFrom: news@techblog.com\\nTo: subscriber@gmail.com\\n\\nHere are the top stories in tech this week..."),
    ("Benign Meeting Invite", "Subject: Project Kickoff\\nFrom: manager@company.com\\nTo: team@company.com\\n\\nLet's meet at 10 AM tomorrow to discuss the new project timeline."),
    ("Benign Lunch Plans", "Subject: Lunch today?\\nFrom: colleague@company.com\\nTo: you@company.com\\n\\nHey, are we still on for lunch at noon?"),
    ("Benign HR Update", "Subject: Holiday Schedule\\nFrom: hr@company.com\\nTo: all@company.com\\n\\nPlease review the upcoming holiday schedule for Q4."),
    ("Benign Code Review", "Subject: Pull Request #42\\nFrom: dev@company.com\\nTo: lead@company.com\\n\\nI've opened a PR for the new feature. Please review when you have time."),
    ("Benign Vendor Follow-up", "Subject: Checking in\\nFrom: account-manager@vendor.com\\nTo: client@company.com\\n\\nJust checking in to see if you have any questions about the software."),
    ("Benign Out of Office", "Subject: OOO: Next Week\\nFrom: coworker@company.com\\nTo: team@company.com\\n\\nI will be out of the office next week. Please contact Jane for urgent matters."),
    ("Benign Server Alert", "Subject: High CPU Usage\\nFrom: monitoring@aws.com\\nTo: devops@company.com\\n\\nServer app-prod-1 is experiencing high CPU usage (90%)."),
    ("Benign Jira Notification", "Subject: [JIRA] Ticket Assigned\\nFrom: jira@company.com\\nTo: dev@company.com\\n\\nTicket PROJ-123 has been assigned to you."),
    ("Benign Social Update", "Subject: Happy Birthday!\\nFrom: team@company.com\\nTo: bob@company.com\\n\\nHappy birthday Bob! There is cake in the breakroom.")
]

all_samples = phishing_samples + benign_samples

def run_tests():
    print("Registering test user...")
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    res = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": "password123", "full_name": "Test User"})
    
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": "password123"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    scan_ids = []
    
    print("Uploading 20 samples...")
    for name, content in all_samples:
        files = {'file': (f'{name.replace(" ", "_")}.eml', content.encode('utf-8'), 'message/rfc822')}
        res = requests.post(f"{BASE_URL}/scans/upload", files=files, headers=headers)
        if res.status_code == 200:
            scan_ids.append((name, res.json()["id"]))
        else:
            print(f"Failed to upload {name}: {res.text}")
            
    print("Waiting 15 seconds for processing...")
    time.sleep(15)
    
    report = []
    
    for name, scan_id in scan_ids:
        res = requests.get(f"{BASE_URL}/scans/{scan_id}", headers=headers)
        if res.status_code == 200:
            data = res.json()
            
            # Aggregate MITRE
            mitre_techniques = []
            detections = data.get("detections", [])
            for d in detections:
                for m in d.get("mitre_mappings", []):
                    mitre_techniques.append(m.get("technique_id"))
                    
            report.append({
                "SampleName": name,
                "ScanID": scan_id,
                "RiskLevel": data.get("risk_level"),
                "OverallRiskScore": data.get("overall_risk_score"),
                "DetectionsTriggered": [d.get("detection_name") for d in detections],
                "EvidenceCount": sum(len(d.get("evidence", [])) for d in detections),
                "RiskContribution": sum(d.get("risk_contribution", 0) for d in detections),
                "MitreTechniques": mitre_techniques
            })
        else:
            print(f"Failed to fetch {scan_id}")
            
    with open("coverage_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Generated coverage_report.json with {len(report)} results.")
    
    for r in report:
        print(f"\\nSample: {r['SampleName']}")
        print(f"Risk Level: {r['RiskLevel']} ({r['OverallRiskScore']})")
        print(f"Detections: {r['DetectionsTriggered']}")
        print(f"MITRE: {r['MitreTechniques']}")
        
if __name__ == "__main__":
    run_tests()
