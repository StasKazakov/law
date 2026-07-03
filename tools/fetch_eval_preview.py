import asyncio
from utils.db_connection import init_db, get_pool, close_db

async def fetch_generated_questions_preview():
    print("Connecting to DB to check generated questions...")
    await init_db()
    pool = get_pool()

    try:
        # Fetch 3 random rows where question is already generated
        rows = await pool.fetch(
            """
            SELECT id, doc_id, cause_num, justice_kind, question
            FROM doc_eval_100
            WHERE question IS NOT NULL
            ORDER BY random()
            LIMIT 3;
            """
        )

        if not rows:
            print("[WARNING] No records found with generated questions.")
            print("Please ensure your main generator script updated the 'question' column.")
            return

        print("\n" + "="*70)
        print("                GENERATED QUESTIONS PREVIEW")
        print("="*70)
        
        for idx, row in enumerate(rows, start=1):
            # Correctly access fields using asyncpg Record format
            print(f"--- Record #{idx} ---")
            print(f"DATABASE ID : {row['id']}")
            print(f"DOCUMENT ID : {row['doc_id']}")
            print(f"CASE NUMBER : {row['cause_num']}")
            print(f"JUSTICE KIND: {row['justice_kind']}")
            print(f"QUESTION    : {row['question']}")
            print("-" * 70)

    except Exception as e:
        print(f"[ERROR] Failed to fetch data: {e}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(fetch_generated_questions_preview())