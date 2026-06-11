import asyncio
from tools.db_connection import init_db, get_pool, close_db

LIMIT_PER_KIND = 50  # 50 admin + 50 commercial = 100 evaluation rows

async def populate_eval_table():
    print("Connecting to DB...")
    await init_db()
    pool = get_pool()

    print("Populating 'doc_eval_100' with 50 admin and 50 commercial rows from 'doc_sample_1k'...")

    async with pool.acquire() as conn:
        
        query = """
            INSERT INTO doc_eval_100 (doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num)
            SELECT doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num
            FROM (
                (SELECT doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num
                 FROM doc_sample_1k
                 WHERE justice_kind = 'admin'
                 ORDER BY random()
                 LIMIT $1)
                UNION ALL
                (SELECT doc_id, doc_url, court_code, judgment_date, text, justice_kind, cause_num
                 FROM doc_sample_1k
                 WHERE justice_kind = 'commercial'
                 ORDER BY random()
                 LIMIT $1)
            ) as combined_samples
            ON CONFLICT (doc_id) DO NOTHING;
        """
        
        result = await conn.execute(query, LIMIT_PER_KIND)
        
        try:
            rows_inserted = int(result.split()[-1])
        except (IndexError, ValueError):
            rows_inserted = 0

        print(f"[FINISHED] Successfully inserted {rows_inserted} rows into 'doc_eval_100'.")

    await close_db()

if __name__ == "__main__":
    asyncio.run(populate_eval_table())