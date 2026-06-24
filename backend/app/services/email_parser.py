"""Email parser — extracts structured data from .eml, .msg, raw paste, and raw headers.

Uses stdlib email for .eml parsing, with optional mail-parser and extract-msg
as enhanced backends (gracefully degraded when unavailable).
"""

from __future__ import annotations

import email
import email.policy
import re
from dataclasses import dataclass, field
from email import message_from_bytes, message_from_string
from email.utils import parseaddr
from io import BytesIO
from typing import Any, Optional

from loguru import logger


@dataclass
class ParsedAttachment:
    filename: str
    content_type: str
    size: int
    content: bytes = field(default_factory=bytes, repr=False)


@dataclass
class ParsedEmail:
    """Structured representation of a parsed email."""
    subject: str = "(no subject)"
    sender_address: str = ""
    sender_display_name: str = ""
    recipient: str = ""
    reply_to: Optional[str] = None
    return_path: Optional[str] = None
    raw_headers: str = ""
    body_text: str = ""
    body_html: str = ""
    parsed_headers: dict[str, Any] = field(default_factory=dict)
    mime_structure: dict[str, Any] = field(default_factory=dict)
    urls: list[str] = field(default_factory=list)
    attachments: list[ParsedAttachment] = field(default_factory=list)


# URL extraction regex
_URL_REGEX = re.compile(
    r'https?://[^\s<>"\')\]}>]+',
    re.IGNORECASE,
)


def _extract_urls(text: str) -> list[str]:
    """Extract unique URLs from text content."""
    found = _URL_REGEX.findall(text or "")
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for url in found:
        url = url.rstrip(".,;:!?)")
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _parse_stdlib(msg: email.message.Message) -> ParsedEmail:
    """Parse an email.message.Message into our dataclass."""
    # Headers
    subject = msg.get("Subject", "(no subject)")
    from_header = msg.get("From", "")
    display_name, sender_addr = parseaddr(from_header)
    _, recipient = parseaddr(msg.get("To", ""))
    reply_to = msg.get("Reply-To")
    return_path = msg.get("Return-Path")

    # Collect all headers
    raw_headers_lines = []
    parsed_headers: dict[str, Any] = {}
    for key in msg.keys():
        value = msg.get(key, "")
        raw_headers_lines.append(f"{key}: {value}")
        if key.lower() in parsed_headers:
            existing = parsed_headers[key.lower()]
            if isinstance(existing, list):
                existing.append(value)
            else:
                parsed_headers[key.lower()] = [existing, value]
        else:
            parsed_headers[key.lower()] = value

    raw_headers = "\n".join(raw_headers_lines)

    # Body extraction
    body_text = ""
    body_html = ""
    attachments: list[ParsedAttachment] = []
    mime_parts: list[dict[str, str]] = []

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            mime_parts.append({"type": ct, "disposition": cd})

            if "attachment" in cd.lower():
                payload = part.get_payload(decode=True) or b""
                attachments.append(ParsedAttachment(
                    filename=part.get_filename() or "unknown",
                    content_type=ct,
                    size=len(payload),
                    content=payload,
                ))
            elif ct == "text/plain" and not body_text:
                body_text = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
            elif ct == "text/html" and not body_html:
                body_html = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
    else:
        ct = msg.get_content_type()
        payload = (msg.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
        if ct == "text/html":
            body_html = payload
        else:
            body_text = payload

    # Extract URLs from both text and html
    all_urls = _extract_urls(body_text) + _extract_urls(body_html)
    # Deduplicate
    seen_urls: set[str] = set()
    unique_urls = []
    for u in all_urls:
        if u not in seen_urls:
            seen_urls.add(u)
            unique_urls.append(u)

    return ParsedEmail(
        subject=subject or "(no subject)",
        sender_address=sender_addr,
        sender_display_name=display_name,
        recipient=recipient,
        reply_to=reply_to,
        return_path=return_path,
        raw_headers=raw_headers,
        body_text=body_text,
        body_html=body_html,
        parsed_headers=parsed_headers,
        mime_structure={"parts": mime_parts},
        urls=unique_urls,
        attachments=attachments,
    )


class EmailParser:
    """Parse emails from various input formats."""

    def parse_eml(self, content: bytes) -> ParsedEmail:
        """Parse .eml file content (RFC 5322)."""
        try:
            # Try mail-parser first (richer parsing)
            import mailparser  # type: ignore
            parsed = mailparser.parse_from_bytes(content)
            msg = message_from_bytes(content, policy=email.policy.default)
            result = _parse_stdlib(msg)
            # Enhance with mail-parser results if available
            if parsed.subject:
                result.subject = parsed.subject
            return result
        except ImportError:
            pass
        except Exception as exc:
            logger.debug(f"mail-parser failed, falling back to stdlib: {exc}")

        # Stdlib fallback
        try:
            msg = message_from_bytes(content, policy=email.policy.default)
            return _parse_stdlib(msg)
        except Exception as exc:
            logger.error(f"Failed to parse .eml: {exc}")
            return ParsedEmail(subject="(parse error)", body_text=content.decode("utf-8", errors="replace"))

    def parse_msg(self, content: bytes) -> ParsedEmail:
        """Parse .msg file content (Outlook format)."""
        try:
            import extract_msg  # type: ignore
            msg = extract_msg.Message(BytesIO(content))
            return ParsedEmail(
                subject=msg.subject or "(no subject)",
                sender_address=msg.sender or "",
                sender_display_name=msg.sender or "",
                recipient=msg.to or "",
                body_text=msg.body or "",
                body_html=msg.htmlBody.decode("utf-8", errors="replace") if msg.htmlBody else "",
                urls=_extract_urls((msg.body or "") + (msg.htmlBody.decode("utf-8", errors="replace") if msg.htmlBody else "")),
                attachments=[
                    ParsedAttachment(
                        filename=att.longFilename or att.shortFilename or "unknown",
                        content_type=att.mimetype or "application/octet-stream",
                        size=len(att.data) if att.data else 0,
                        content=att.data or b"",
                    )
                    for att in (msg.attachments or [])
                ],
            )
        except ImportError:
            logger.warning("extract-msg not installed; .msg parsing unavailable")
            return ParsedEmail(
                subject="(msg parsing unavailable)",
                body_text="The extract-msg library is required to parse .msg files.",
            )
        except Exception as exc:
            logger.error(f"Failed to parse .msg: {exc}")
            return ParsedEmail(subject="(parse error)")

    def parse_raw(self, content: str) -> ParsedEmail:
        """Parse raw pasted email content (full RFC 5322 or plain text)."""
        # If it looks like RFC 5322 (has headers), parse as such
        if re.match(r"^[A-Za-z-]+:\s", content):
            try:
                msg = message_from_string(content, policy=email.policy.default)
                return _parse_stdlib(msg)
            except Exception:
                pass

        # Fallback: treat as plain body text
        # Try to extract any sender/subject-like info from first lines
        lines = content.strip().split("\n")
        subject = "(pasted content)"
        sender = ""
        body_lines = []
        for line in lines:
            lower = line.lower().strip()
            if lower.startswith("subject:") and subject == "(pasted content)":
                subject = line.split(":", 1)[1].strip()
            elif lower.startswith("from:") and not sender:
                _, sender = parseaddr(line.split(":", 1)[1].strip())
            else:
                body_lines.append(line)

        body_text = "\n".join(body_lines)
        return ParsedEmail(
            subject=subject,
            sender_address=sender,
            body_text=body_text,
            urls=_extract_urls(body_text),
        )

    def parse_headers_only(self, raw_headers: str) -> ParsedEmail:
        """Parse raw headers only — no body content."""
        # Construct a minimal email message from headers
        try:
            msg = message_from_string(raw_headers + "\n\n", policy=email.policy.default)
            result = _parse_stdlib(msg)
            result.body_text = ""
            result.body_html = ""
            result.raw_headers = raw_headers
            return result
        except Exception as exc:
            logger.error(f"Failed to parse headers: {exc}")
            return ParsedEmail(raw_headers=raw_headers)
