"""Security utilities — HTML sanitisation, input validation helpers."""

from __future__ import annotations

import html
import re
from typing import Optional


def sanitize_html(raw_html: str) -> tuple[str, list[str]]:
    """Sanitize HTML content for safe rendering in a sandbox viewer.

    Returns (sanitized_html, warnings).
    Strips scripts, event handlers, iframes, objects, embeds, and data URIs.
    """
    warnings: list[str] = []
    if not raw_html:
        return "", warnings

    sanitized = raw_html

    # Remove script tags
    script_pattern = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
    if script_pattern.search(sanitized):
        warnings.append("Script tags removed")
        sanitized = script_pattern.sub("<!-- [script removed] -->", sanitized)

    # Remove event handlers
    event_pattern = re.compile(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE)
    if event_pattern.search(sanitized):
        warnings.append("Inline event handlers removed")
        sanitized = event_pattern.sub("", sanitized)

    # Remove iframes
    iframe_pattern = re.compile(r"<iframe[\s\S]*?(?:</iframe>|/>)", re.IGNORECASE)
    if iframe_pattern.search(sanitized):
        warnings.append("Iframes removed")
        sanitized = iframe_pattern.sub("<!-- [iframe removed] -->", sanitized)

    # Remove object/embed tags
    obj_pattern = re.compile(r"<(?:object|embed|applet)[\s\S]*?(?:</(?:object|embed|applet)>|/>)", re.IGNORECASE)
    if obj_pattern.search(sanitized):
        warnings.append("Embedded objects removed")
        sanitized = obj_pattern.sub("<!-- [object removed] -->", sanitized)

    # Remove data: URIs (potential XSS vector)
    data_uri_pattern = re.compile(r'(src|href)\s*=\s*["\']data:[^"\']*["\']', re.IGNORECASE)
    if data_uri_pattern.search(sanitized):
        warnings.append("Data URIs removed")
        sanitized = data_uri_pattern.sub('\\1=""', sanitized)

    # Remove javascript: URIs
    js_uri_pattern = re.compile(r'(href|src)\s*=\s*["\']javascript:[^"\']*["\']', re.IGNORECASE)
    if js_uri_pattern.search(sanitized):
        warnings.append("JavaScript URIs removed")
        sanitized = js_uri_pattern.sub('\\1="#"', sanitized)

    # Remove meta refresh
    meta_pattern = re.compile(r'<meta[^>]*http-equiv\s*=\s*["\']refresh["\'][^>]*>', re.IGNORECASE)
    if meta_pattern.search(sanitized):
        warnings.append("Meta refresh tags removed")
        sanitized = meta_pattern.sub("<!-- [meta-refresh removed] -->", sanitized)

    # Remove form tags (but keep content)
    form_pattern = re.compile(r"</?form[^>]*>", re.IGNORECASE)
    if form_pattern.search(sanitized):
        warnings.append("Form tags removed (content preserved)")
        sanitized = form_pattern.sub("", sanitized)

    # Neutralise external links (add target=_blank and rel=noopener)
    link_pattern = re.compile(r"(<a\s)", re.IGNORECASE)
    sanitized = link_pattern.sub(r'\1target="_blank" rel="noopener noreferrer" ', sanitized)

    return sanitized, warnings


def is_valid_email(email: str) -> bool:
    """Quick regex check for email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def extract_domain(email_or_url: str) -> Optional[str]:
    """Extract the domain portion from an email address or URL."""
    if "@" in email_or_url:
        return email_or_url.split("@")[-1].strip().lower()
    try:
        from urllib.parse import urlparse
        parsed = urlparse(email_or_url)
        return parsed.hostname or None
    except Exception:
        return None
