import asyncio
from tqdm import tqdm
from config import BATCH_SIZE, EMBEDDING_MODEL, VECTOR_COLUMN
from google.genai import types
from utils.db_connection import init_db, get_pool, close_db
from utils.clients import gemini_client
from utils.db_handlers import (
    fetch_chunks_without_embeddings,
    get_missing_embeddings_count,
    update_chunk_embeddings,
)


async def process_batch(pool, rows, target_column: str):
    """Fetches 3072-dimension text embeddings from Gemini API and updates the database."""
    chunk_ids = [row["id"] for row in rows]
    texts = [row["chunk_text"] for row in rows]

    try:
        response = await asyncio.to_thread(
            gemini_client.models.embed_content,
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=3072),
        )

        update_data = []
        for idx, embedding in enumerate(response.embeddings):
            vector = str(embedding.values)
            chunk_id = chunk_ids[idx]
            update_data.append((vector, chunk_id))

        await update_chunk_embeddings(
            pool, update_data, column_name=target_column
        )

    except Exception as e:
        print(f"\n❌ Error processing batch via Gemini: {e}")
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
    print("🏁 Gemini embedding generation process completed!")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())