import asyncio
from utils.db_connection import init_db, get_pool, close_db
from config import EMBEDDING_MODEL
from utils.clients import gemini_client, openai_client, openrouter_client, lm_studio
from google.genai import types

# Get questions from database
async def fetching_questions():
    try:
        pool = get_pool()
        
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, document_id, question_text FROM questions_42;"
            )
            
            questions_list = []
            for row in rows:
                questions_list.append({
                    "id": row["id"],
                    "target_document_id": int(row["document_id"]),
                    "text": row["question_text"]
                })
            
            return questions_list

    except Exception as e:
        print(f"❌ Error while fetching questions: {e}")
# Create embeddings with Gemini
async def get_gemini_embedding(text: str) -> str:
    """Fetches a 3072-dimension embedding vector from Gemini for the given text."""
    response = await asyncio.to_thread(
        gemini_client.models.embed_content,
        model=EMBEDDING_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=3072),
    )

    return str(response.embeddings[0].values)
# Get top 10 documents
async def get_top_10_documents(question_embedding: str, vector_column: str) -> list:
    pool = get_pool()
    
    search_query = f"""
        SELECT doc_id 
        FROM chunks_1024 
        GROUP BY doc_id 
        ORDER BY MIN({vector_column} <=> $1::vector) 
        LIMIT 10;
    """
    
    async with pool.acquire() as connection:
        rows = await connection.fetch(search_query, question_embedding)
        return [int(row['doc_id']) for row in rows]
# Calculate MRR
def calculate_linear_rank_score(top_documents: list, target_doc_id: int) -> float:
    for rank, doc_id in enumerate(top_documents, start=1):
        if doc_id == target_doc_id:
            return (11 - rank) / 10.0
    return 0.0
# Save results in database
async def save_benchmark_result(final_score: float, model_column: str, chunk_size: str) -> None:
    """
    Updates the benchmark table for a specific model column and chunk size.
    """
    pool = get_pool()
    
    update_query = f"""
        UPDATE benchmark 
        SET {model_column} = $1 
        WHERE chunk_size = $2;
    """
    
    async with pool.acquire() as connection:
        await connection.execute(update_query, final_score, chunk_size)
# Create embeddings with OpenAI
async def get_openai_embedding(text: str) -> str:
    """Fetches a 3072-dimension embedding vector from OpenAI for the given text."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=[text],
        dimensions=3072
    )
    return str(response.data[0].embedding)
# Create embeddings with Qwen
async def get_qwen_embedding(text: str) -> str:
    """Fetches a 4096-dimension embedding vector from OpenRouter for the given text."""
    response = await openrouter_client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL,
    )
    return str(response.data[0].embedding)
# Create embeddings with LM Studio
async def get_lm_studio_embedding(text: str) -> str:

    response = await lm_studio.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL
    )
    return str(response.data[0].embedding)