import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import async_session_factory
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.core.auth import hash_password
from sqlalchemy import select
import uuid
import pyotp
import getpass

async def create_platform_admin():
    print("\n--- PhishGuard AI: Platform Admin Bootstrap ---")
    email = input("Email: ").strip()
    full_name = input("Full Name: ").strip()
    
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    
    if password != confirm_password:
        print("\n[ERROR] Passwords do not match.")
        sys.exit(1)
        
    if len(password) < 12:
        print("\n[ERROR] Password must be at least 12 characters.")
        sys.exit(1)

    async with async_session_factory() as session:
        # Check if email exists
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"\n[ERROR] User with email {email} already exists.")
            sys.exit(1)
            
        print("\nGenerating MFA Secret...")
        totp_secret = pyotp.random_base32()
        
        # Create user
        admin = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=UserRole.admin,
            is_active=True,
            mfa_enabled=True,
            totp_secret=totp_secret
        )
        session.add(admin)
        await session.flush()
        
        # Create default root organization
        org = Organization(
            name="PhishGuard HQ",
            slug=f"hq-{uuid.uuid4().hex[:8]}",
            plan="enterprise",
            is_active=True
        )
        session.add(org)
        await session.flush()
        
        # Make admin member of HQ
        member = OrganizationMember(
            organization_id=org.id,
            user_id=admin.id,
            role=OrganizationRole.platform_admin,
            is_active=True
        )
        session.add(member)
        
        await session.commit()
        
    print("\n[SUCCESS] Platform Admin created successfully.")
    print("-" * 50)
    print(f"User: {email}")
    print(f"MFA Secret (Save this securely): {totp_secret}")
    print("MFA URL:")
    print(pyotp.totp.TOTP(totp_secret).provisioning_uri(name=email, issuer_name="PhishGuard AI"))
    print("-" * 50)
    print("Bootstrap complete. Ensure this secret is imported into your authenticator app.")

if __name__ == "__main__":
    asyncio.run(create_platform_admin())
