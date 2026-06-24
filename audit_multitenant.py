import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import uuid

DATABASE_URL = "postgresql+asyncpg://phishguard:phishguard_secret@localhost:5433/phishguard_db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def audit_multitenant():
    async with async_session() as db:
        print("--- PART 4: MULTI-TENANT VERIFICATION ---")
        
        # 1. Check schemas
        print("\n1. Schemas enforcing isolation:")
        for table in ["saved_searches", "tracked_entities", "recent_searches"]:
            res = await db.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'user_id';
            """))
            row = res.fetchone()
            print(f"  {table} has column: {row[0]} ({row[1]})")
        
        # 2. Create Users A and B
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        
        await db.execute(text("""
            INSERT INTO users (id, email, full_name, hashed_password, role, is_active, created_at, updated_at)
            VALUES (:id_a, 'usera@example.com', 'User A', 'hash', 'analyst', true, now(), now()),
                   (:id_b, 'userb@example.com', 'User B', 'hash', 'analyst', true, now(), now())
        """), {"id_a": user_a_id, "id_b": user_b_id})
        
        # 3. Create records for User A
        await db.execute(text("""
            INSERT INTO saved_searches (id, user_id, name, query, created_at)
            VALUES (:sid, :uid, 'My Search', 'domain:paypal', now())
        """), {"sid": uuid.uuid4(), "uid": user_a_id})
        
        await db.execute(text("""
            INSERT INTO tracked_entities (id, user_id, entity_type, entity_value, added_at)
            VALUES (:tid, :uid, 'ioc', 'paypal-secure.com', now())
        """), {"tid": uuid.uuid4(), "uid": user_a_id})
        
        await db.commit()
        
        # 4. Verify isolation
        print("\n2. Verification:")
        # User A
        res_a = await db.execute(text("SELECT name FROM saved_searches WHERE user_id = :uid"), {"uid": user_a_id})
        print(f"  User A Saved Searches: {[r[0] for r in res_a]}")
        res_a_t = await db.execute(text("SELECT entity_value FROM tracked_entities WHERE user_id = :uid"), {"uid": user_a_id})
        print(f"  User A Tracked IOCs: {[r[0] for r in res_a_t]}")
        
        # User B
        res_b = await db.execute(text("SELECT name FROM saved_searches WHERE user_id = :uid"), {"uid": user_b_id})
        print(f"  User B Saved Searches: {[r[0] for r in res_b]}")
        res_b_t = await db.execute(text("SELECT entity_value FROM tracked_entities WHERE user_id = :uid"), {"uid": user_b_id})
        print(f"  User B Tracked IOCs: {[r[0] for r in res_b_t]}")

asyncio.run(audit_multitenant())
