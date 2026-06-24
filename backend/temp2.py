from app.detections.registry import DetectionRuleBase
from app.detections.models import DetectionResult, DetectionSeverity, MitreMapping
import re

class CredentialHarvestingRule(DetectionRuleBase):
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        evidence = []
        matched_patterns = []
        
        body = scan.body_text.lower() if scan.body_text else ""
        html = scan.body_html.lower() if scan.body_html else ""
        subject = scan.subject.lower() if scan.subject else ""
        sender = scan.sender_address.lower() if scan.sender_address else ""
        
        # 0. Ignore legitimate workflows
        if "reset" in subject and "password" in subject and not scan.reply_to:
            # Often legit password resets have no reply-to or matching domains, but let's just use heuristic
            if "requested a password reset" in body:
                # Need to be careful. We will ignore if it's from a trusted corporate domain.
                # For simplicity, if it's a standard password reset text, we require stronger evidence.
                pass
                
        # 1. Login Request
        login_keywords = ["verify your account", "login to continue", "update your billing", "password expiry", "sign in", "secure gateway", "access document", "verification"]
        has_login = False
        for kw in login_keywords:
            if kw in combined_text or kw in subject:
                has_login = True
                matched_patterns.append(kw)
                
        # 2. Credential Collection Intent (Forms)
        has_collection = False
        has_external_dest = False
        
        if "<form" in combined_text and ("password" in combined_text or "type='password'" in combined_text or 'type="password"' in combined_text):
            has_collection = True
            matched_patterns.append("password_form")
            
        # Or links that look like login portals
        link_keywords = ["login", "auth", "signin", "verify", "secure"]
        for lkw in link_keywords:
            if lkw in combined_text and "href=" in combined_text:
                has_collection = True
                matched_patterns.append("login_link")
                
                urls = re.findall(r"href=['\"]([^'\"]+)['\"]", combined_text)
                for url in urls:
                    if url.startswith("http") and "company.com" not in url:
                        has_external_dest = True
                        matched_patterns.append("external_login_link")
                        evidence.append(f"Contains link to external login page: {url}")
                break
            
        # 3. External Destination
        form_actions = re.findall(r"action=['\"]([^'\"]+)['\"]", combined_text)
        for action in form_actions:
            if action.startswith("http") and "company.com" not in action:
                has_external_dest = True
                matched_patterns.append("external_form_action")
                evidence.append(f"Form submits to external URL: {action}")
                
        is_password_form = "password_form" in matched_patterns
                
        if (has_login and has_collection and has_external_dest) or (is_password_form and has_external_dest):
            if not has_login:
                evidence.append("External credential collection form detected without explicit login keywords")
            else:
                evidence.append("Login request combined with external credential collection form")
            
            return DetectionResult(
                detection_name="Credential Harvesting Attempt",
                category="Credential Harvesting",
                severity=DetectionSeverity.high,
                confidence=95,
                risk_contribution=45.0,
                matched_patterns=matched_patterns,
                mitre_mappings=[
                    MitreMapping(technique_id="T1566.002", name="Spearphishing Link", tactic="Initial Access"),
                    MitreMapping(technique_id="T1040", name="Network Sniffing", tactic="Credential Access")
                ],
                evidence=evidence,
                explanation="The email requests login or account verification and includes a form or link that submits data to an external, untrusted destination."
            )
            
        return None