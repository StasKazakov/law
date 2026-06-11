import asyncio
from tools.db_connection import init_db, get_pool, close_db

async def fetch_row_500():
    print("Connecting to DB to fetch row #500...")
    await init_db()
    pool = get_pool()

    try:
        # Fetch the 500th row using OFFSET
        # Sorting by id ensures we get a deterministic 500th record
        row = await pool.fetchrow(
            """
            SELECT id, doc_id, doc_url, court_code, judgment_date, text, created_at, justice_kind, cause_num 
            FROM doc_eval_100 
            ORDER BY id 
            LIMIT 1 OFFSET 99;
            """
        )


        if not row:
            print("[WARNING] Row #500 not found. Maybe the table has fewer rows?")
            return

        print("\n" + "="*50)
        print("          DATA FROM ROW #500")
        print("="*50)
        print(f"Internal DB ID:  {row['id']}")
        print(f"Court Doc ID:    {row['doc_id']}")
        print(f"Court Code:      {row['court_code']}")
        print(f"Judgment Date:   {row['judgment_date']}")
        print(f"Doc URL:         {row['doc_url']}")
        print(f"Parsed At:       {row['created_at']}")
        print(f"Justice Kind:    {row['justice_kind']}")
        print(f"Case Number:     {row['cause_num']}")
        print("="*50)
        
        # Print the first 1000 characters of the text to check quality
        text_preview = row['text']
        print("CLEAN TEXT PREVIEW (First 1000 chars):")
        print("-" * 50)
        if len(text_preview) > 1000:
            print(text_preview[:1000] + "\n\n[... TEXT TRUNCATED FOR PREVIEW ...]")
        else:
            print(text_preview)
        print("-" * 50)

    except Exception as e:
        print(f"[ERROR] Failed to fetch data: {e}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(fetch_row_500())