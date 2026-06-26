import asyncio
from utils.db_connection import init_db, get_pool, close_db
from config import EMBEDDING_MODEL
from utils.clients import gemini_client
from google.genai import types

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
    
async def get_gemini_embedding(text: str) -> str:
    """Fetches a 3072-dimension embedding vector from Gemini for the given text."""
    response = await asyncio.to_thread(
        gemini_client.models.embed_content,
        model=EMBEDDING_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=3072),
    )

    return str(response.embeddings[0].values)

async def get_top_10_documents(question_embedding: str) -> list:
    pool = get_pool()
    
    search_query = """
        SELECT doc_id 
        FROM doc_chunks_1k 
        GROUP BY doc_id 
        ORDER BY MIN(gemini_vector <=> $1::vector) 
        LIMIT 10;
    """
    
    async with pool.acquire() as connection:
        rows = await connection.fetch(search_query, question_embedding)
        return [int(row['doc_id']) for row in rows]

def calculate_mrr_score(top_documents: list, target_doc_id: int) -> float:
    for rank, doc_id in enumerate(top_documents, start=1):
        if doc_id == target_doc_id:
            return 1.0 / rank
    return 0.0

async def save_benchmark_result(final_score: float) -> None:
    pool = get_pool()
    
    update_query = """
        UPDATE benchmark 
        SET gemini = $1 
        WHERE chunk_size = '256';
    """
    
    async with pool.acquire() as connection:
        await connection.execute(update_query, final_score)