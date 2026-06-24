import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# App configuration
DATABASE_URL = "postgresql+asyncpg://phishguard:phishguard_secret@localhost:5433/phishguard_db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def audit_relationships():
    async with async_session() as db:
        print("--- PART 1: RELATIONSHIP ENGINE PROOF ---")
        
        # 1. Schema
        print("\n1. Relationship Table Schema:")
        schema_query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'relationships';
        """)
        res = await db.execute(schema_query)
        for row in res:
            print(f"  {row[0]}: {row[1]}")
            
        # 2. Count
        print("\n2. Relationship Row Count:")
        count_query = text("SELECT COUNT(*) FROM relationships;")
        res = await db.execute(count_query)
        print(f"  Count: {res.scalar()}")
        
        # 3. Sample Rows
        print("\n3. Sample Rows:")
        sample_query = text("""
            SELECT source_type, source_value, target_type, target_value, relationship_type, confidence 
            FROM relationships 
            LIMIT 5;
        """)
        res = await db.execute(sample_query)
        for row in res:
            print(f"  {row[0]} -> {row[2]} | {row[1]} <-> {row[3]} | Type: {row[4]} | Conf: {row[5]}")

asyncio.run(audit_relationships())
