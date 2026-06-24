import re
from typing import Dict, Any, List
from urllib.parse import urlparse

from app.models.ioc import EmailIoc, IocType

class IocExtractor:
    def __init__(self):
        # Regex for common IOCs
        self.ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
        self.md5_pattern = re.compile(r'\b[a-fA-F0-9]{32}\b')
        self.sha1_pattern = re.compile(r'\b[a-fA-F0-9]{40}\b')
        self.sha256_pattern = re.compile(r'\b[a-fA-F0-9]{64}\b')
        self.crypto_pattern = re.compile(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b|\b0x[a-fA-F0-9]{40}\b')
        self.phone_pattern = re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
        self.message_id_pattern = re.compile(r'Message-ID:\s*(<[^>]+>)', re.IGNORECASE)

    def extract(self, scan_id: str, parsed_email: Dict[str, Any]) -> List[EmailIoc]:
        iocs = []
        seen = set()

        def add_ioc(ioc_type: IocType, value: str):
            value = value.strip().lower()
            if not value or value in seen:
                return
            seen.add(value)
            iocs.append(EmailIoc(scan_id=scan_id, ioc_type=ioc_type, value=value))

        # 1. Sender and Reply-To
        sender = parsed_email.get("sender_address", "")
        if sender:
            add_ioc(IocType.email, sender)
            domain = sender.split('@')[-1] if '@' in sender else ""
            if domain:
                add_ioc(IocType.sender_domain, domain)
                add_ioc(IocType.domain, domain)

        reply_to = parsed_email.get("reply_to", "")
        if reply_to:
            add_ioc(IocType.email, reply_to)
            domain = reply_to.split('@')[-1] if '@' in reply_to else ""
            if domain:
                add_ioc(IocType.reply_to_domain, domain)

        # 2. Extract from URLs
        urls = parsed_email.get("urls", [])
        for url in urls:
            add_ioc(IocType.url, url)
            try:
                parsed = urlparse(url)
                if parsed.hostname:
                    add_ioc(IocType.domain, parsed.hostname)
                    # Check if hostname is an IP
                    if self.ip_pattern.match(parsed.hostname):
                        add_ioc(IocType.ip, parsed.hostname)
            except Exception:
                pass

        # 3. Extract from body text
        body = parsed_email.get("body_text", "")
        if body:
            # IPs
            for ip in self.ip_pattern.findall(body):
                add_ioc(IocType.ip, ip)
            
            # Emails
            for email in self.email_pattern.findall(body):
                add_ioc(IocType.email, email)
                
            # Hashes
            for md5 in self.md5_pattern.findall(body):
                add_ioc(IocType.md5, md5)
            for sha1 in self.sha1_pattern.findall(body):
                add_ioc(IocType.sha1, sha1)
            for sha256 in self.sha256_pattern.findall(body):
                add_ioc(IocType.sha256, sha256)
            for crypto in self.crypto_pattern.findall(body):
                add_ioc(IocType.cryptocurrency_wallet, crypto)
            for phone in self.phone_pattern.findall(body):
                # Simple filter to avoid matching random long numbers as phones
                if len(re.sub(r'\D', '', phone)) >= 7:
                    add_ioc(IocType.phone_number, phone)

        # 4. Attachments
        attachments = parsed_email.get("attachments", [])
        for att in attachments:
            name = att.get("filename", "")
            if name:
                add_ioc(IocType.attachment_name, name)
                if '.' in name:
                    ext = name.split('.')[-1]
                    add_ioc(IocType.attachment_extension, ext)
                    
            if att.get("md5"):
                add_ioc(IocType.md5, att.get("md5"))
            if att.get("sha256"):
                add_ioc(IocType.sha256, att.get("sha256"))

        # 5. Extract IPs from headers (basic)
        raw_headers = parsed_email.get("raw_headers", "")
        if raw_headers:
            for ip in self.ip_pattern.findall(raw_headers):
                # Ignore common local IPs
                if not (ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.") or ip.startswith("172.16.")):
                    add_ioc(IocType.ip, ip)
            message_id_match = self.message_id_pattern.search(raw_headers)
            if message_id_match:
                add_ioc(IocType.message_id, message_id_match.group(1))

        return iocs
