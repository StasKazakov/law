from db_connection import init_db, get_pool, close_db

async def list_tables(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
    return [row['table_name'] for row in rows]

pool = await init_db()
tables = await list_tables(pool)
print(tables)