import asyncio
# Import functions from your db_connection.py file
from db_connection import init_db, get_pool, close_db

async def run_test():
    print("Step 1: Initializing database pool...")
    try:
        await init_db()
    except Exception as e:
        print(f"[FAIL] Initialization failed. Check your .env file. Error: {e}")
        return

    print("\nStep 2: Acquiring connection and testing query...")
    try:
        pool = get_pool()
        # Acquire a temporary connection from the pool
        async with pool.acquire() as connection:
            # Query our newly created table to check permissions
            row_count = await connection.fetchval("SELECT COUNT(*) FROM documents;")
            print(f"[SUCCESS] Connected! Current row count in 'documents' table: {row_count}")
            
            # Additional check: get current database user name
            current_user = await connection.fetchval("SELECT current_user;")
            print(f"[INFO] Authenticated as user: {current_user}")
            
    except Exception as e:
        print(f"[FAIL] Database query failed. Check server status or permissions. Error: {e}")
    finally:
        print("\nStep 3: Closing database pool...")
        await close_db()

if __name__ == "__main__":
    # Start the async loop
    asyncio.run(run_test())