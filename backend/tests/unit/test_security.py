"""Unit tests for security primitives. No database or Redis required."""

import pytest

from app.core.security import safe_filename, sanitize_html


@pytest.mark.parametrize(
    "payload",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        '<a href="javascript:alert(1)">x</a>',
        '<a href=" JaVaScRiPt:alert(1)">x</a>',
        '<iframe src="https://evil"></iframe>',
        '<div style="background:url(https://evil/p.png)">x</div>',
        '<meta http-equiv="refresh" content="0;url=https://evil">',
        "<form action=https://evil><input name=p></form>",
    ],
)
def test_sanitizer_strips_active_content(payload):
    out, _ = sanitize_html(payload)
    lowered = out.lower()
    for bad in ("<script", "onerror", "onload", "javascript:", "<iframe", "url(", "<meta", "<form", "<input", "<svg"):
        assert bad not in lowered


def test_sanitizer_blocks_remote_images_but_keeps_text():
    out, warnings = sanitize_html('<p>Hello <img src="https://tracker/p.gif"> world</p>')
    assert "Hello" in out and "world" in out
    assert ' src=' not in out
    assert "Remote images blocked" in warnings


def test_sanitizer_keeps_safe_links_with_noopener():
    out, _ = sanitize_html('<a href="https://example.com">x</a>')
    assert 'href="https://example.com"' in out
    assert "noopener" in out


def test_safe_filename_strips_paths():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("C:\\Users\\a\\evil.eml") == "evil.eml"
    assert safe_filename("") == "unnamed"
