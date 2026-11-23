import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from app.database import SessionLocal
from app.models.graph import Relationship, EntityType
from app.models.scan import EmailScan

async def main():
    async with SessionLocal() as db:
        # We will add the column in migration, then run this backfill
        pass

if __name__ == "__main__":
    asyncio.run(main())
