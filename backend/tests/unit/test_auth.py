"""Auth helper tests (JWT, refresh rotation, API keys, password policy)."""

import asyncio

import pytest
from fastapi import HTTPException

from app.core import auth


def run(coro):
    return asyncio.run(coro)


def test_access_token_roundtrip():
    token = auth.create_access_token("11111111-1111-1111-1111-111111111111", "org", "SOC Analyst")
    payload = auth.decode_token(token)
    assert payload["sub"].startswith("1111")
    assert payload["type"] == "access"


def test_refresh_token_cannot_be_used_as_access():
    token = run(auth.create_refresh_token("u1"))
    with pytest.raises(HTTPException):
        auth.decode_token(token)  # expects type=access


def test_refresh_token_is_single_use():
    async def scenario():
        token = await auth.create_refresh_token("u1")
        await auth.consume_refresh_token(token)
        with pytest.raises(HTTPException):
            await auth.consume_refresh_token(token)

    run(scenario())


def test_revoked_refresh_token_rejected():
    async def scenario():
        token = await auth.create_refresh_token("u2")
        await auth.revoke_refresh_token(token)
        with pytest.raises(HTTPException):
            await auth.consume_refresh_token(token)

    run(scenario())


def test_tampered_token_rejected():
    token = auth.create_access_token("u", "o", "r")
    with pytest.raises(HTTPException):
        auth.decode_token(token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1])


def test_api_key_hash_verification():
    raw, hashed, prefix = auth.generate_api_key()
    assert raw.startswith("pg_") and prefix == raw[:8]
    assert auth._verify_api_key(raw, hashed)
    assert not auth._verify_api_key(raw + "x", hashed)


@pytest.mark.parametrize(
    "password,ok",
    [("short", False), ("alllowercaseletters", False), ("Correct-Horse-42", True), ("PhishGuard@2024!", False)],
)
def test_password_policy(password, ok):
    assert (auth.password_policy_errors(password, "analyst@example.com") == []) is ok
