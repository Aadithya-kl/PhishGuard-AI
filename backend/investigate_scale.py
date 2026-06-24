import asyncio
from sqlalchemy import select, func
from app.database import async_session_factory
from app.models.scan import EmailScan
from app.models.ioc import EmailIoc
from app.models.graph import Relationship

async def run_investigation():
    async with async_session_factory() as db:
        scan_count = await db.scalar(select(func.count(EmailScan.id)))
        ioc_count = await db.scalar(select(func.count(EmailIoc.id)))
        rel_count = await db.scalar(select(func.count(Relationship.id)))
        
        print(f"Total Scans: {scan_count}")
        print(f"Total IOCs: {ioc_count}")
        print(f"Total Relationships: {rel_count}")

if __name__ == "__main__":
    asyncio.run(run_investigation())
