import asyncio
from tools.db_connection import init_db, get_pool, close_db

BATCH_SIZE = 50000  

async def migrate_data(target_table: str, justice_kind: str):
    print("🛜  Connecting to DB...")
    await init_db()
    pool = get_pool()

    print(f"🏁  Starting copy for '{justice_kind}' into '{target_table}'...")
    
    offset = 0
    total_moved = 0

    while True:
        async with pool.acquire() as conn:
            query = f"""
                INSERT INTO {target_table} (doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num)
                SELECT doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num
                FROM doc_2025
                WHERE justice_kind = $1
                ORDER BY id
                LIMIT $2 OFFSET $3
                ON CONFLICT (doc_id) DO NOTHING;
            """
            
            result = await conn.execute(query, justice_kind, BATCH_SIZE, offset)
            
            try:
                rows_affected = int(result.split()[-1])
            except (IndexError, ValueError):
                rows_affected = 0

            if rows_affected == 0:
                check = await conn.fetchval(
                    f"SELECT 1 FROM doc_2025 WHERE justice_kind = $1 LIMIT 1 OFFSET $2;", 
                    justice_kind, offset
                )
                if not check:
                    break

            total_moved += rows_affected
            print(f"🚀 Copy {total_moved} rows into '{target_table}' (Current offset: {offset})...")
            
            offset += BATCH_SIZE

    print(f"🏁 Migration completed! Total rows moved into '{target_table}': {total_moved}")
    await close_db()

if __name__ == "__main__":
    asyncio.run(migrate_data(target_table="commercial_2025", justice_kind="commercial"))
    
