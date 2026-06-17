import asyncio
from tqdm import tqdm
from config import BATCH_SIZE, EMBEDDING_MODEL, VECTOR_COLUMN
from utils.clients import lm_studio
from utils.db_connection import init_db, get_pool, close_db
from utils.db_handlers import get_missing_embeddings_count, fetch_chunks_without_embeddings, update_chunk_embeddings


async def process_batch(pool, rows, target_column: str):
    """Fetches embeddings from LM Studio and delegates database writing."""
    chunk_ids = [row["id"] for row in rows]
    texts = [row["chunk_text"] for row in rows]

    try:
        response = await lm_studio.embeddings.create(
            input=texts, model=EMBEDDING_MODEL
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
        print(f"\n❌ Error processing batch: {e}")
        raise e


async def main():
    await init_db()
    pool = get_pool()

    total_to_process = await get_missing_embeddings_count(pool, VECTOR_COLUMN)

    print(
        f"📊 Total chunks remaining for {VECTOR_COLUMN} processing: {total_to_process}"
    )

    if total_to_process == 0:
        print("✅ All embeddings are already generated!")
        await close_db()
        return

    pbar = tqdm(
        total=total_to_process,
        desc="🚀 Generating vectors",
        unit="chunk",
        ncols=100,
    )

    while True:
        rows = await fetch_chunks_without_embeddings(
            pool, VECTOR_COLUMN, BATCH_SIZE
        )

        if not rows:
            break

        try:
            await process_batch(pool, rows, VECTOR_COLUMN)
            pbar.update(len(rows))
        except Exception:
            print("\n❌ Execution stopped due to an error.")
            break

    pbar.close()
    print("🏁 Embedding generation process completed!")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())