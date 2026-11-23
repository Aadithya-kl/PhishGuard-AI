import os
import sys

# Make "app" importable and force a deterministic, non-production config for tests.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256-0123456789")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:1/0")  # unreachable -> in-memory token store
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@127.0.0.1:1/db")
