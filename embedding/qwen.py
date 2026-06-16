import asyncio
from openai import AsyncOpenAI
from tqdm import tqdm
from tools.db_connection import init_db, get_pool, close_db

BATCH_SIZE = 32
MODEL_NAME = "text-embedding-qwen3-embedding-8b"

local_client = AsyncOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"  
)

async def process_batch(pool, rows):
    """Fetches embeddings from LM Studio and updates the database."""
    chunk_ids = [row["id"] for row in rows]
    texts = [row["chunk_text"] for row in rows]
    
    try:
        response = await local_client.embeddings.create(
            input=texts,
            model=MODEL_NAME
        )
        
        update_data = []
        for idx, item in enumerate(response.data):
            vector = item.embedding
            chunk_id = chunk_ids[idx]
            update_data.append((vector, chunk_id))
            
        await pool.executemany(
            """
            UPDATE doc_chunks_1k
            SET qwen_vector = $1
            WHERE id = $2;
            """,
            update_data
        )
    except Exception as e:
        print(f"\n❌ Error processing batch: {e}")
        raise e

async def main():
    await init_db()
    pool = get_pool()
    
    count_row = await pool.fetchrow(
        "SELECT COUNT(*) FROM doc_chunks_1k WHERE qwen_vector IS NULL;"
    )
    total_to_process = count_row["count"]
    
    print(f"📊 Total chunks remaining for Qwen processing: {total_to_process}")
    
    if total_to_process == 0:
        print("✅ All embeddings are already generated!")
        await close_db()
        return

    pbar = tqdm(
        total=total_to_process, 
        desc="Generating Qwen vectors", 
        unit="chunk", 
        ncols=100
    )
    
    while True:
        rows = await pool.fetch(
            """
            SELECT id, chunk_text 
            FROM doc_chunks_1k 
            WHERE qwen_vector IS NULL 
            ORDER BY id 
            LIMIT $1;
            """,
            BATCH_SIZE
        )
        
        if not rows:
            break  
            
        try:
            await process_batch(pool, rows)
            pbar.update(len(rows))
        except Exception:

            print("\n❌ Execution stopped due to an error.")
            break
        
    pbar.close()
    print("🏁 Embedding generation process completed!")
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())