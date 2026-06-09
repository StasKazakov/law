import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

_pool = None

async def init_db():
    """
    Initializes the PostgreSQL connection pool using credentials from .env.
    This should be called once when the application starts.
    """
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                min_size=2,  
                max_size=10  
            )
            print("[DB] Connection pool initialized successfully.")
        except Exception as e:
            print(f"[DB ERROR] Failed to initialize connection pool: {e}")
            raise e
    return _pool

def get_pool():
    """
    Returns the initialized pool. 
    Raises an error if init_db() wasn't called first.
    """
    if _pool is None:
        raise RuntimeError("Database pool has not been initialized. Call 'await init_db()' first.")
    return _pool

async def close_db():
    """Closes the connection pool gracefully when the script terminates."""
    global _pool
    if _pool is not None:
        await _pool.close()
        print("[DB] Connection pool closed.")
        _pool = None


async def get_total_documents_count() -> int:
    """
    Connects to the database using the existing pool and returns 
    the total number of rows in the 'documents' table.
    """
    try:
        pool = get_pool()
        count = await pool.fetchval("SELECT COUNT(*) FROM documents;")
        print(f"[DB] Total rows in 'documents' table: {count}")
        return count
        
    except Exception as e:
        print(f"[DB ERROR] Failed to fetch row count: {e}")
        return 0