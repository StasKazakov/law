import asyncio
import re
from utils.db_connection import get_pool, init_db, close_db

def clean_text_strict(text: str) -> str:
    """
    Removes only \xa0, redundant spaces, and extra newlines.
    """
    if not text:
        return ""
    # 1. Replace non-breaking spaces (\xa0) with standard spaces
    text = text.replace("\xa0", " ")
    # 2. Collapse multiple spaces or tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)
    # 3. Collapse 3 or more consecutive newlines into exactly two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

async def clean_database_table():
    """
    Fetches all 1000 rows, cleans them in memory, and updates via a single query execution.
    """
    # Using your existing initialized database pool
    pool = get_pool()
    
    async with pool.acquire() as conn:
        print("📥 Fetching all 1000 documents from doc_sample_1k...")
        rows = await conn.fetch("SELECT doc_id, text FROM doc_sample_1k")
        
        # Prepare all data at once in memory
        update_data = []
        for row in rows:
            cleaned = clean_text_strict(row['text'])
            update_data.append((cleaned, row['doc_id']))
        
        if update_data:
            print(f"⚡ Updating {len(update_data)} records in the database at once...")
            # Updating everything in a single database round-trip
            await conn.executemany(
                "UPDATE doc_sample_1k SET text = $1 WHERE doc_id = $2", 
                update_data
            )
            print("🎉 Done! All texts successfully cleaned.")
        else:
            print("ℹ️ No documents required cleaning.")

async def main():
    # If pool is already active globally, you can remove init_db/close_db
    await init_db()
    try:
        await clean_database_table()
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())