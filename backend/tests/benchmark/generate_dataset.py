import os
import email
from email.message import EmailMessage
import random
import uuid

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

base_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(base_dir, "dataset")
ensure_dir(dataset_dir)
ensure_dir(os.path.join(dataset_dir, "benign"))
ensure_dir(os.path.join(dataset_dir, "phishing"))

def create_eml(folder, prefix, subject, sender, to, body, is_html=False, extra_headers=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg["Message-ID"] = f"<{uuid.uuid4()}@{sender.split('@')[-1]}>"
    msg["Date"] = email.utils.formatdate(localtime=True)
    
    if extra_headers:
        for k, v in extra_headers.items():
            msg[k] = v
            
    if is_html:
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)
        
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.eml"
    filepath = os.path.join(dataset_dir, folder, filename)
    with open(filepath, "wb") as f:
        f.write(bytes(msg))
    return filepath

# Generators
def generate_synthetic_benign(count=50):
    for i in range(count):
        create_eml(
            "benign",
            "synth",
            f"Weekly Project Update {i}",
            "colleague@internal.company.com",
            "you@company.com",
            f"Here is the project update for week {i}. Everything is on track.",
            extra_headers={"Authentication-Results": "spf=pass dkim=pass dmarc=pass"}
        )

def generate_synthetic_phishing(count=50):
    for i in range(count):
        create_eml(
            "phishing",
            "synth",
            f"URGENT: Password Reset Required {i}",
            "security@paypal-update.tk",
            "you@company.com",
            f"<html><body>Click <a href='http://192.168.1.100/login'>here</a> to reset.</body></html>",
            is_html=True,
            extra_headers={"Authentication-Results": "spf=fail dkim=fail"}
        )

def generate_real_benign(count=20):
    templates = [
        ("GitHub: [company/repo] New pull request", "notifications@github.com", "User has opened a new pull request #42. https://github.com/company/repo/pull/42"),
        ("Google: Security alert", "no-reply@accounts.google.com", "A new sign-in from Chrome on Windows was detected. If this was you, ignore this email."),
        ("Microsoft: Daily Briefing", "briefing@microsoft.com", "Here's what's happening today. You have 3 meetings."),
        ("LinkedIn: You have 5 new connections", "messages-noreply@linkedin.com", "Expand your network. Click here to view connections: https://linkedin.com/"),
        ("Amazon: Your order has shipped", "shipment-tracking@amazon.com", "Order #123-456-789 has shipped. Track it at https://amazon.com/track")
    ]
    for i in range(count):
        subject, sender, body = templates[i % len(templates)]
        create_eml("benign", "real", subject, sender, "you@company.com", body, extra_headers={"Authentication-Results": "spf=pass dkim=pass dmarc=pass"})

def generate_real_phishing(count=20):
    templates = [
        ("GitHub: Account Suspension Notice", "security@github-support.com", "<html><body>Your GitHub account will be suspended. <a href='http://xn--gthub-1sa.com/login'>Verify now</a></body></html>"),
        ("Google: Action Required: Payment Declined", "billing@accounts-google.net", "<html><body>Update your payment method: <a href='http://104.28.14.32/pay'>Update</a></body></html>"),
        ("Microsoft 365: Password Expires in 24 hours", "admin@microsoft365-updates.com", "<html><body>Keep same password: <a href='http://ms-login-update.com/'>Click here</a></body></html>"),
        ("LinkedIn: View urgent document", "messages@linkedin-docs.com", "<html><body>View the secure document here: <a href='http://evil.com/doc.exe'>Document</a></body></html>"),
        ("Amazon: Order Cancellation Required", "support@amazon-refunds.com", "<html><body>Cancel order here: <a href='http://amazon-refunds.com/cancel'>Cancel</a></body></html>")
    ]
    for i in range(count):
        subject, sender, body = templates[i % len(templates)]
        create_eml("phishing", "real", subject, "billing@paypal.com", "you@company.com", body, is_html=True, extra_headers={"Authentication-Results": "spf=fail dkim=fail", "Return-Path": "<attacker@evil.com>"})

if __name__ == "__main__":
    print("Generating dataset...")
    generate_synthetic_benign(50)
    generate_synthetic_phishing(50)
    generate_real_benign(20)
    generate_real_phishing(20)
    print("Dataset generated successfully at", dataset_dir)
