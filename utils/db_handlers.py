async def update_chunk_embeddings(pool, update_data, column_name):
    """Updates the specified column with generated embeddings in a bulk operation."""
    query = f"""
        UPDATE chunks_1024
        SET {column_name} = $1
        WHERE id = $2;
    """

    await pool.executemany(query, update_data)

async def get_missing_embeddings_count(pool, column_name) -> int:
    """Counts how many chunks are missing embeddings for the specified column."""
    query = f"SELECT COUNT(*) FROM chunks_1024 WHERE {column_name} IS NULL;"
    row = await pool.fetchrow(query)
    return row["count"]

async def fetch_chunks_without_embeddings(pool, column_name, limit) -> list:
    """Fetches a batch of chunks that don't have embeddings for the specified column."""
    query = f"""
        SELECT id, chunk_text 
        FROM chunks_1024 
        WHERE {column_name} IS NULL 
        ORDER BY id 
        LIMIT $1;
    """
    return await pool.fetch(query, limit)