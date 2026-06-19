# embedding/euler_embedding.py
import asyncio
from tqdm import tqdm
from utils.clients import euler_client
from utils.db_connection import init_db, get_pool, close_db
from utils.db_handlers import get_missing_embeddings_count, fetch_chunks_without_embeddings, update_chunk_embeddings
from config import BATCH_SIZE, EMBEDDING_MODEL, VECTOR_COLUMN

async def fetch_single_embedding(text: str, chunk_id: int) -> list:
    """
    Fetches a single embedding vector using AsyncOpenAI client.
    Now that CUDA is fixed, this will run at maximum speed.
    """
    try:
        response = await euler_client.embeddings.create(
            input=text, 
            model=EMBEDDING_MODEL,
            timeout=30.0
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"\n❌ [Chunk ID: {chunk_id}] API Error: {e}")
        raise

async def process_batch(pool, rows, target_column: str):
    """Fetches embeddings concurrently using asyncio.gather and updates the DB."""
    chunk_ids = [row["id"] for row in rows]
    texts = [row["chunk_text"] for row in rows]

    tasks = [fetch_single_embedding(text, chunk_ids[idx]) for idx, text in enumerate(texts)]
    vectors = await asyncio.gather(*tasks)
    update_data = []
    for idx, vector in enumerate(vectors):
        chunk_id = chunk_ids[idx]
        update_data.append((str(vector), chunk_id))

    await update_chunk_embeddings(pool, update_data, column_name=target_column)

async def main():
    print("🔄 Step 1: Initializing database connection pool...")
    await init_db()
    pool = get_pool()

    print(f"🔎 Step 2: Counting remaining chunks for column '{VECTOR_COLUMN}'...")
    total_to_process = await get_missing_embeddings_count(pool, VECTOR_COLUMN)
    print(f"📊 Total chunks remaining for processing: {total_to_process}")

    if total_to_process == 0:
        print("✅ All Euler embeddings are already generated!")
        await close_db()
        return

    print(f"🚀 Step 3: Starting async processing loop (Batch Size: {BATCH_SIZE})...")
    pbar = tqdm(
        total=total_to_process,
        desc="⚙️ Generating Euler vectors",
        unit="chunk",
        ncols=100,
    )

    batch_counter = 0
    while True:
        batch_counter += 1
        rows = await fetch_chunks_without_embeddings(pool, VECTOR_COLUMN, BATCH_SIZE)

        if not rows:
            print("\n🏁 All chunks processed successfully!")
            break

        try:
            
            await process_batch(pool, rows, VECTOR_COLUMN)
            pbar.update(len(rows))
            await asyncio.sleep(0.05)
            
        except Exception as e:
            print(f"\n❌ Process stopped due to an error in batch #{batch_counter}: {e}")
            break

    pbar.close()
    await close_db()
    print("🏁 Euler embedding generation process completed!")

if __name__ == "__main__":
    asyncio.run(main())