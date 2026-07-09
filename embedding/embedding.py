import asyncio
from tqdm import tqdm
from config import BATCH_SIZE, EMBEDDING_MODEL, VECTOR_COLUMN
from utils.db_connection import init_db, get_pool, close_db
from utils.clients import openrouter_client
from utils.db_handlers import (
    fetch_chunks_without_embeddings,
    get_missing_embeddings_count,
    update_chunk_embeddings,
)


async def process_batch(pool, rows, target_column: str):
    
    chunk_ids = [row["id"] for row in rows]
    texts = [row["chunk_text"] for row in rows]

    try:
        response = await openrouter_client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL,
        )

        update_data = []
        for idx, item in enumerate(response.data):
            vector = str(item.embedding)
            chunk_id = chunk_ids[idx]
            update_data.append((vector, chunk_id))
        await update_chunk_embeddings(
            pool, update_data, column_name=target_column
        )

    except Exception as e:
        print(f"\n❌ Error processing batch for column '{target_column}' via OpenRouter: {e}")
        raise e


async def main():
    await init_db()
    pool = get_pool()

    total_to_process = await get_missing_embeddings_count(pool, VECTOR_COLUMN)

    print(
        f"📊 Total chunks remaining for [{VECTOR_COLUMN}] processing: {total_to_process}"
    )

    if total_to_process == 0:
        print(f"✅ All embeddings for [{VECTOR_COLUMN}] are already generated!")
        await close_db()
        return

    pbar = tqdm(
        total=total_to_process,
        desc=f"🚀 Generating {VECTOR_COLUMN} vectors",
        unit="chunk",
        ncols=100,
    )

    while True:
        
        rows_needed = BATCH_SIZE * 5
        all_rows = await fetch_chunks_without_embeddings(
            pool, VECTOR_COLUMN, rows_needed
        )

        if not all_rows:
            print(f"\n⚡ No more rows without embeddings for [{VECTOR_COLUMN}].")
            break

        
        tasks = []
        for i in range(0, len(all_rows), BATCH_SIZE):
            batch_rows = all_rows[i : i + BATCH_SIZE]
            
            tasks.append(process_batch(pool, batch_rows, VECTOR_COLUMN))

        try:
            await asyncio.gather(*tasks)
            pbar.update(len(all_rows))
        except Exception as e:
            print(f"\n❌ Execution stopped due to a parallel processing error: {e}")
            break


if __name__ == "__main__":
    asyncio.run(main())