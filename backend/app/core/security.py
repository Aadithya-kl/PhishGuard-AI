"""Security utilities — allow-list HTML sanitiser and small validation helpers.

The sanitiser is used to build the *email preview* that analysts see. Phishing
HTML is hostile by definition, so this is defence in depth: the frontend also
renders the result inside a sandboxed ``<iframe>`` with a CSP that blocks all
scripts and all network fetches (no tracking pixels reach the attacker).
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urlparse

_ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "center", "code", "div", "em", "font", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre", "s", "small", "span", "strong",
    "sub", "sup", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul",
}
_VOID_TAGS = {"br", "hr", "img"}
_DROP_CONTENT_TAGS = {"script", "style", "iframe", "object", "embed", "applet", "noscript", "template",
                      "svg", "math", "form", "frameset", "frame", "base", "link", "meta", "title", "head"}
_ALLOWED_ATTRS = {"align", "alt", "bgcolor", "border", "cellpadding", "cellspacing", "color", "colspan",
                  "height", "href", "rowspan", "src", "style", "title", "valign", "width"}
_SAFE_SCHEMES = {"http", "https", "mailto", ""}
_STYLE_BLOCK = re.compile(r"expression|javascript:|url\s*\(|@import|behavior\s*:|-moz-binding", re.I)


class _Sanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.warnings: set[str] = set()
        self.links: list[str] = []
        self._drop_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS:
            if tag not in _VOID_TAGS and tag not in {"meta", "link", "base"}:
                self._drop_depth += 1
            self.warnings.add(f"<{tag}> removed")
            return
        if self._drop_depth or tag not in _ALLOWED_TAGS:
            return
        clean: list[str] = []
        for name, value in attrs:
            name = (name or "").lower()
            value = value or ""
            if name.startswith("on"):
                self.warnings.add("Inline event handlers removed")
                continue
            if name not in _ALLOWED_ATTRS:
                continue
            if name in {"href", "src"}:
                scheme = urlparse(value.strip()).scheme.lower()
                if scheme not in _SAFE_SCHEMES:
                    self.warnings.add(f"{scheme or 'unknown'}: URI removed")
                    continue
                if name == "href":
                    self.links.append(value)
                if name == "src":
                    # Remote images are tracking beacons — never load them.
                    self.warnings.add("Remote images blocked")
                    clean.append(f'data-blocked-src="{html.escape(value, quote=True)}"')
                    continue
            if name == "style" and _STYLE_BLOCK.search(value):
                self.warnings.add("Dangerous CSS removed")
                continue
            clean.append(f'{name}="{html.escape(value, quote=True)}"')
        if tag == "a":
            clean.append('target="_blank" rel="noopener noreferrer nofollow"')
        self.out.append(f"<{tag}{(' ' + ' '.join(clean)) if clean else ''}>")

    def handle_startendtag(self, tag, attrs):
        if tag.lower() in _DROP_CONTENT_TAGS:
            self.warnings.add(f"<{tag.lower()}> removed")
            return
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _DROP_CONTENT_TAGS:
            self._drop_depth = max(0, self._drop_depth - 1)
            return
        if self._drop_depth or tag not in _ALLOWED_TAGS or tag in _VOID_TAGS:
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self._drop_depth:
            self.out.append(html.escape(data, quote=False))

    def handle_comment(self, data):
        return  # drop comments (conditional comments can carry payloads)


def sanitize_html(raw_html: str, max_len: int = 2_000_000) -> tuple[str, list[str]]:
    """Return (sanitised_html, warnings) using a strict allow-list."""
    if not raw_html:
        return "", []
    parser = _Sanitizer()
    try:
        parser.feed(raw_html[:max_len])
        parser.close()
    except Exception:
        return f"<pre>{html.escape(raw_html[:max_len])}</pre>", ["HTML could not be parsed; shown as text"]
    return "".join(parser.out), sorted(parser.warnings)


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def extract_domain(email_or_url: str) -> Optional[str]:
    if "@" in email_or_url and "://" not in email_or_url:
        return email_or_url.split("@")[-1].strip().lower()
    try:
        return urlparse(email_or_url).hostname or None
    except Exception:
        return None


def safe_filename(name: str, max_len: int = 200) -> str:
    """Strip path components and control characters from an uploaded filename."""
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    return (name or "unnamed")[:max_len]
