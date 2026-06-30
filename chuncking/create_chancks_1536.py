import asyncio
import tiktoken
from tqdm import tqdm
from utils.db_connection import init_db, get_pool, close_db  

CHUNK_SIZE    = 1536
CHUNK_OVERLAP = 300   
EMBED_MODEL   = "universal"
STRATEGY      = f"size{CHUNK_SIZE}_ov{CHUNK_OVERLAP}_token"

enc = tiktoken.get_encoding("o200k_base")


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []

    cleaned_text = " ".join(text.split()).strip()

    tokens = enc.encode(cleaned_text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)

        if end >= len(tokens):
            break

        start += chunk_size - overlap  

    return chunks


async def process_documents():
    pool = get_pool()

    rows = await pool.fetch("SELECT doc_id, text FROM doc_sample_1k ORDER BY id;")
    print(f"✅ Loaded documents from sample: {len(rows)}")

    total_chunks = 0

    pbar = tqdm(
        total=len(rows), desc="Processing documents into 1024 chunks", unit="doc", ncols=100
    )

    for row in rows:
        doc_id = row["doc_id"]
        text   = row["text"]

        if not text or not text.strip():
            print(f"[WARN] Empty text for doc_id={doc_id}, skipping.")
            continue

        chunks = split_into_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)

        await pool.executemany(
            """
            INSERT INTO chunks_1536
                (doc_id, chunk_index, chunk_text, embed_model, strategy, chunk_size, chunk_overlap)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            [
                (doc_id, idx, chunk, EMBED_MODEL, STRATEGY, CHUNK_SIZE, CHUNK_OVERLAP)
                for idx, chunk in enumerate(chunks)
            ]
        )

        total_chunks += len(chunks)
        pbar.update(1)

    pbar.close()
    print(f"🏁 Generation completed! Total chunks written to 'chunks_1536': {total_chunks}")


async def main():
    await init_db()
    try:
        await process_documents()
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())