import asyncio
import tiktoken
from tqdm import tqdm
from utils.db_connection import init_db, get_pool, close_db  

CHUNK_SIZE    = 512
CHUNK_OVERLAP = 100   
enc = tiktoken.get_encoding("o200k_base")


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text:
        return []

    lines = [" ".join(line.split()).strip() for line in text.splitlines()]
    paragraphs = [line for line in lines if line]
    
    chunks, current_tokens, current_text = [], [], []

    for para in paragraphs:
        para_tokens = enc.encode(para + "\n")
        
        if len(para_tokens) > chunk_size:
            if current_text:
                chunks.append("".join(current_text).strip())
                current_tokens, current_text = [], []
            start = 0
            while start < len(para_tokens):
                chunks.append(enc.decode(para_tokens[start:start + chunk_size]).strip())
                start += chunk_size - overlap
            continue

        if len(current_tokens) + len(para_tokens) > chunk_size:
            chunks.append("".join(current_text).strip())
            overlap_tokens = current_tokens[-overlap:] if overlap < len(current_tokens) else current_tokens
            current_tokens = list(overlap_tokens) + para_tokens
            current_text = [enc.decode(overlap_tokens), para + "\n"]
        else:
            current_tokens.extend(para_tokens)
            current_text.append(para + "\n")

    if current_text:
        chunks.append("".join(current_text).strip())

    return chunks


async def process_documents():
    pool = get_pool()
    rows = await pool.fetch("SELECT doc_id, text FROM doc_sample_1k ORDER BY id;")
    print(f"✅ Loaded documents from sample: {len(rows)}")

    total_chunks = 0
    pbar = tqdm(total=len(rows), desc="Processing documents", unit="doc", ncols=100)

    for row in rows:
        doc_id = int(row["doc_id"])
        text = row["text"]

        if not text or not text.strip():
            pbar.update(1)
            continue

        chunks = split_into_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)

        await pool.executemany(
            """
            INSERT INTO doc_embeddings (doc_id, chunk_index, chunk_text, embedding)
            VALUES ($1, $2, $3, $4)
            """,
            [(doc_id, idx, chunk, None) for idx, chunk in enumerate(chunks)]
        )

        total_chunks += len(chunks)
        pbar.update(1)

    pbar.close()
    print(f"🏁 Generation completed! Total chunks written: {total_chunks}")


async def main():
    await init_db()
    try:
        await process_documents()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())