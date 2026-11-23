"""Operational CLI.

Usage (inside the backend container)::

    python -m app.cli migrate                 # create/upgrade the schema
    python -m app.cli create-admin            # interactive
    python -m app.cli create-admin --email a@b.com --name "Ada" --org "Acme SOC"   # password from PHISHGUARD_ADMIN_PASSWORD

``migrate`` is idempotent: on an empty database it creates every table from the
models and stamps Alembic at head; on an existing one it runs ``alembic upgrade head``.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import re
import sys
import uuid

from sqlalchemy import inspect, select


async def _has_tables() -> bool:
    from app.database import engine

    async with engine.connect() as conn:
        return await conn.run_sync(lambda c: "users" in inspect(c).get_table_names())


def migrate() -> None:
    from alembic import command
    from alembic.config import Config

    from app.database import init_db

    cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    if not asyncio.run(_has_tables()):
        print("[migrate] empty database — creating schema from models")
        asyncio.run(init_db())
        command.stamp(cfg, "head")
    else:
        print("[migrate] existing database — running alembic upgrade head")
        command.upgrade(cfg, "head")
    print("[migrate] done")


async def _create_admin(email: str, name: str, password: str, org_name: str, mfa: bool) -> None:
    import pyotp

    from app.core.auth import hash_password, password_policy_errors
    from app.database import async_session_factory
    from app.models.organization import Organization, OrganizationMember, OrganizationRole, PlanTier
    from app.models.user import User, UserRole

    errors = password_policy_errors(password, email)
    if errors:
        sys.exit(f"[error] Password {', '.join(errors)}")

    async with async_session_factory() as session:
        if (await session.execute(select(User).where(User.email == email))).scalar_one_or_none():
            sys.exit(f"[error] A user with e-mail {email} already exists")
        secret = pyotp.random_base32() if mfa else None
        user = User(
            email=email,
            full_name=name,
            hashed_password=hash_password(password),
            role=UserRole.admin,
            is_active=True,
            mfa_enabled=mfa,
            totp_secret=secret,
        )
        session.add(user)
        await session.flush()
        slug = re.sub(r"[^a-z0-9]+", "-", org_name.lower()).strip("-")[:40] or "org"
        org = Organization(name=org_name, slug=f"{slug}-{uuid.uuid4().hex[:6]}", plan=PlanTier.enterprise, is_active=True)
        session.add(org)
        await session.flush()
        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=OrganizationRole.platform_admin, is_active=True))
        await session.commit()

    print(f"[ok] Platform admin {email} created in organization '{org_name}'.")
    if mfa:
        uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="PhishGuard AI")
        print(f"[ok] MFA is ON. Add this to your authenticator app now:\n     {uri}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="Create or upgrade the database schema")
    ca = sub.add_parser("create-admin", help="Create the first platform administrator")
    ca.add_argument("--email")
    ca.add_argument("--name")
    ca.add_argument("--org", default="PhishGuard HQ")
    ca.add_argument("--mfa", action="store_true", help="Enable TOTP MFA immediately")
    args = parser.parse_args(argv)

    if args.cmd == "migrate":
        migrate()
    elif args.cmd == "create-admin":
        email = (args.email or input("Email: ")).strip().lower()
        name = (args.name or input("Full name: ")).strip()
        password = os.environ.get("PHISHGUARD_ADMIN_PASSWORD") or getpass.getpass("Password: ")
        if not os.environ.get("PHISHGUARD_ADMIN_PASSWORD") and getpass.getpass("Confirm password: ") != password:
            sys.exit("[error] Passwords do not match")
        asyncio.run(_create_admin(email, name, password, args.org, args.mfa))


if __name__ == "__main__":
    main()
