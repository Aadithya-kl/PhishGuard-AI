import asyncio
import uuid
from datetime import datetime, timedelta, timezone
import random

from sqlalchemy import select
from app.database import async_session_factory
from app.models.user import User
from app.models.scan import EmailScan, HeaderAnalysis, UrlAnalysis, AttachmentAnalysis, AiAnalysis, RiskLevel, ScanStatus, SeverityLevel
from app.models.ioc import EmailIoc, IocType

CAMPAIGNS = [
    {
        "name": "PayPal Brand Impersonation",
        "type": "Brand Impersonation",
        "sender_domains": ["paypa1-update.com", "billing-paypal-secure.com"],
        "urls": ["http://paypal-login-secure-update.com/login", "https://paypal.auth-verify-account.com"],
        "ips": ["192.168.100.15", "10.0.55.23"],
        "risk": RiskLevel.high,
        "subjects": ["[DEMO] Urgent: Your account has been suspended", "[DEMO] Action Required: Verify your PayPal activity"]
    },
    {
        "name": "Invoice Malware Delivery",
        "type": "Malware Delivery",
        "sender_domains": ["invoice-processing.net", "accounts-payable-dept.com"],
        "urls": ["http://download-invoice-secure.net/payload.exe"],
        "ips": ["45.33.22.11"],
        "hashes": ["d41d8cd98f00b204e9800998ecf8427e", "e99a18c428cb38d5f260853678922e03"],
        "risk": RiskLevel.high,
        "subjects": ["[DEMO] Invoice #88493 Overdue", "[DEMO] Payment Remittance Advice"]
    },
    {
        "name": "CEO BEC Fraud",
        "type": "Business Email Compromise",
        "sender_domains": ["ceo-urgent-request.com", "exec-board-internal.net"],
        "reply_to": ["ceo@ceo-urgent-request.com"],
        "ips": ["104.22.11.99"],
        "risk": RiskLevel.high,
        "subjects": ["[DEMO] Urgent Wire Transfer Needed", "[DEMO] Are you at your desk?"]
    },
    {
        "name": "M365 Credential Harvest",
        "type": "Credential Harvesting",
        "sender_domains": ["m365-alert-center.com", "office365-security-update.com"],
        "urls": ["http://login.microsoftonline-auth.net/login", "https://m365-password-reset.com"],
        "ips": ["8.8.8.8", "1.1.1.1"], # Fake IPs for demo
        "risk": RiskLevel.suspicious,
        "subjects": ["[DEMO] Password Expiry Notice", "[DEMO] Required security update for your mailbox"]
    },
    {
        "name": "Benign Newsletters",
        "type": "Benign",
        "sender_domains": ["marketing.benign.com", "news.tech-updates.com"],
        "urls": ["https://marketing.benign.com/article1", "https://tech-updates.com/news"],
        "ips": ["142.250.190.46"],
        "risk": RiskLevel.safe,
        "subjects": ["[DEMO] Your Weekly Tech Digest", "[DEMO] Updates for June 2026"]
    }
]

async def generate():
    async with async_session_factory() as session:
        # Get or create admin user
        result = await session.execute(select(User).where(User.email == "admin@phishguard.ai"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="admin@phishguard.ai",
                hashed_password="fake",
                full_name="Admin",
                role="admin",
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # Generate 100 scans
        print("Generating 100 demo scans...")
        now = datetime.now(timezone.utc)
        
        for i in range(100):
            camp = random.choice(CAMPAIGNS)
            scanned_at = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 24))
            
            sender_domain = random.choice(camp["sender_domains"])
            sender_address = f"info@{sender_domain}"
            
            scan = EmailScan(
                user_id=user.id,
                subject=random.choice(camp["subjects"]),
                sender_address=sender_address,
                sender_display_name="Notification",
                recipient="employee@company.com",
                attack_type=camp["type"],
                risk_level=camp["risk"],
                overall_risk_score=random.uniform(70, 95) if camp["risk"] != RiskLevel.safe else random.uniform(0, 15),
                status=ScanStatus.completed,
                scanned_at=scanned_at
            )
            session.add(scan)
            await session.flush()
            
            # Header Analysis
            ip = random.choice(camp["ips"]) if "ips" in camp else "127.0.0.1"
            reply_to = random.choice(camp["reply_to"]) if "reply_to" in camp else sender_address
            header = HeaderAnalysis(
                scan_id=scan.id,
                spf_result="fail" if camp["risk"] != RiskLevel.safe else "pass",
                dkim_result="fail" if camp["risk"] != RiskLevel.safe else "pass",
                sender_spoofed=camp["risk"] != RiskLevel.safe,
                evidence={"source_ip": ip, "reply_to": reply_to}
            )
            session.add(header)
            
            # IOCs for IP and Sender Domain
            session.add(EmailIoc(scan_id=scan.id, ioc_type=IocType.ip, value=ip, threat_score=80.0 if camp["risk"] != RiskLevel.safe else 0.0))
            session.add(EmailIoc(scan_id=scan.id, ioc_type=IocType.sender_domain, value=sender_domain, threat_score=75.0 if camp["risk"] != RiskLevel.safe else 0.0))
            
            if "urls" in camp:
                url_val = random.choice(camp["urls"])
                url_domain = url_val.split("/")[2]
                url_obj = UrlAnalysis(
                    scan_id=scan.id,
                    original_url=url_val,
                    domain=url_domain,
                    risk_score=85.0 if camp["risk"] != RiskLevel.safe else 0.0
                )
                session.add(url_obj)
                session.add(EmailIoc(scan_id=scan.id, ioc_type=IocType.url, value=url_val, threat_score=85.0 if camp["risk"] != RiskLevel.safe else 0.0))
                session.add(EmailIoc(scan_id=scan.id, ioc_type=IocType.domain, value=url_domain, threat_score=85.0 if camp["risk"] != RiskLevel.safe else 0.0))
            
            if "hashes" in camp:
                h = random.choice(camp["hashes"])
                att_obj = AttachmentAnalysis(
                    scan_id=scan.id,
                    filename="invoice.pdf.exe",
                    content_type="application/x-msdownload",
                    md5_hash=h,
                    threat_score=95.0
                )
                session.add(att_obj)
                session.add(EmailIoc(scan_id=scan.id, ioc_type=IocType.md5, value=h, threat_score=95.0))
                
            # Ai Analysis
            ai = AiAnalysis(
                scan_id=scan.id,
                model_used="gemini-2.0-flash",
                attack_classification=camp["type"],
                severity_level=SeverityLevel.high if camp["risk"] == RiskLevel.high else SeverityLevel.low,
                confidence_score=0.9,
                executive_summary=f"Demo summary for {camp['name']}",
                technical_summary="Demo technical details."
            )
            session.add(ai)
            
        await session.commit()
        print("Demo data generated successfully.")

if __name__ == "__main__":
    asyncio.run(generate())
