import asyncio
from utils.db_connection import init_db, get_pool, close_db
from hybrid_search.fts_engine import build_index


async def fetch_all_chunks():
    pool = get_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT doc_id, chunk_text FROM chunks_512;"
        )
        return [(row["doc_id"], row["chunk_text"]) for row in rows]


async def main():
    try:
        await init_db()
        print("Take chunks from chunks_512...")
        doc_chunks = await fetch_all_chunks()
        print(f"Recived {len(doc_chunks)} chunks.")
        build_index(doc_chunks)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())