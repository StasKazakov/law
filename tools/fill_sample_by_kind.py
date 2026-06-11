import asyncio
from tools.db_connection import init_db, get_pool, close_db

LIMIT_SIZE = 500  # Number of random rows to fetch from each table

async def fill_sample_from_table(source_table: str):
    print("Connecting to DB...")
    await init_db()
    pool = get_pool()

    print(f"Fetching {LIMIT_SIZE} random rows from '{source_table}' and inserting into 'doc_sample_1k'...")

    async with pool.acquire() as conn:
        # Dynamic query using ORDER BY random() to grab balanced test cases
        query = f"""
            INSERT INTO doc_sample_1k (doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num)
            SELECT doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num
            FROM {source_table}
            ORDER BY random()
            LIMIT $1
            ON CONFLICT (doc_id) DO NOTHING;
        """
        
        result = await conn.execute(query, LIMIT_SIZE)
        
        try:
            rows_inserted = int(result.split()[-1])
        except (IndexError, ValueError):
            rows_inserted = 0

        print(f"[PROGRESS] Successfully added {rows_inserted} rows from '{source_table}' into 'doc_sample_1k'.")

    await close_db()

if __name__ == "__main__":
    
    asyncio.run(fill_sample_from_table(source_table="commercial_2025"))
    
