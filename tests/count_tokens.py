import asyncio
import statistics
import tiktoken
from dotenv import load_dotenv
from tools.db_connection import init_db, get_pool, close_db

load_dotenv()

async def main():
    pool = await init_db()
    if not pool:
        pool = get_pool()

    print("Fetching all documents...")

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT text FROM doc_sample_1k;")

        print(f"Documents loaded: {len(rows)}")

        enc = tiktoken.get_encoding("o200k_base")
        token_counts = []

        for i, row in enumerate(rows, 1):
            cleaned = " ".join(row["text"].split())
            tokens = enc.encode(cleaned)
            token_counts.append(len(tokens))

            if i % 100 == 0:
                print(f"  Processed {i}/{len(rows)}...")

        print("-" * 50)
        print(f"📊 Total documents : {len(token_counts)}")
        print(f"📊 Average tokens  : {sum(token_counts) / len(token_counts):.1f}")
        print(f"📊 Median tokens   : {statistics.median(token_counts):.1f}")
        print(f"📊 Min tokens      : {min(token_counts)}")
        print(f"📊 Max tokens      : {max(token_counts)}")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())