import asyncio
from hybrid_search.fts_engine import search_fts
from utils.db_connection import init_db, get_pool, close_db
from config import EMBEDDING_MODEL
from utils.clients import gemini_client, openai_client, openrouter_client, lm_studio, euler_client
from google.genai import types
from typing import List, Dict


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
# Get top documents
async def get_top_documents(question_embedding: str, vector_column: str, limit: int = 10) -> list:
    pool = get_pool()
    raw_limit = limit * 3
    search_query = f"""
        SELECT doc_id 
        FROM chunks_512
        ORDER BY {vector_column} <=> $1::vector 
        LIMIT {raw_limit};
    """
    
    async with pool.acquire() as connection:
        rows = await connection.fetch(search_query, question_embedding)
        
        seen_docs = set()
        unique_doc_ids = []
        
        for row in rows:
            doc_id = int(row['doc_id'])
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_doc_ids.append(doc_id)
                
            # Stop as soon as we collected the requested number of unique documents
            if len(unique_doc_ids) == limit:
                break
                
        return unique_doc_ids
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

async def get_euler_embedding(text: str) -> list:
    """Fetches embedding from the Euler endpoint using the shared client."""
    response = await euler_client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL
    )
    
    return str(response.data[0].embedding)

async def fetch_best_chunks_for_documents(pool, doc_ids: list, question_embedding: str, vector_column: str) -> list:
   
    if not doc_ids:
        return []
    
    query = f"""
        WITH best_chunks AS (
            SELECT DISTINCT ON (doc_id) doc_id, chunk_text
            FROM chunks_512
            WHERE doc_id = ANY($1::varchar[])
            ORDER BY doc_id, {vector_column} <=> $2::vector
        )
        SELECT chunk_text 
        FROM best_chunks
        ORDER BY array_position($1::varchar[], doc_id);
    """
    string_ids = [str(d) for d in doc_ids]
    
    rows = await pool.fetch(query, string_ids, question_embedding)
    return [row['chunk_text'] for row in rows]

async def fetch_full_documents(pool, doc_ids: List[int]) -> Dict[int, str]:
    if not doc_ids:
        return {}

    string_ids = []
    for d_id in doc_ids:
        if isinstance(d_id, (tuple, list)):
            string_ids.append(str(d_id[0]))
        else:
            string_ids.append(str(d_id))

    query = """
        SELECT doc_id, text 
        FROM doc_sample_1k 
        WHERE doc_id = ANY($1::text[])
    """
    
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, string_ids)
            
            result_map = {int(row['doc_id']): (row['text'] or "") for row in rows}
            clean_int_ids = [int(x) for x in string_ids]
            missing_ids = set(clean_int_ids) - set(result_map.keys())
            if missing_ids:
                print(f"⚠️ Warning: Missing full text for document IDs: {list(missing_ids)}")
                
            return result_map
            
    except Exception as e:
        print(f"❌ Error while fetching full documents from database: {str(e)}")
        return {}
    
async def new_get_top_documents(question_embedding: str, vector_column: str, limit: int = 10) -> list:
    pool = get_pool()
    
    raw_limit = 200  
    
    search_query = f"""
        SELECT DISTINCT ON (doc_id) doc_id
        FROM (
            SELECT doc_id, ({vector_column} <=> $1::vector) as distance
            FROM chunks_512
            ORDER BY {vector_column} <=> $1::vector 
            LIMIT {raw_limit}
        ) sub
        ORDER BY doc_id, distance
        LIMIT {limit};
    """
    
    async with pool.acquire() as connection:
        rows = await connection.fetch(search_query, question_embedding)
        return [row["doc_id"] for row in rows]
    
# Get only problem questions.
async def fetching_problem_questions():
    try:
        pool = get_pool()
        problematic_ids = [2, 7, 9, 14, 15, 16, 17, 24, 34, 37, 38, 42]
        
        async with pool.acquire() as connection:
            
            rows = await connection.fetch(
                "SELECT id, document_id, question_text FROM questions_42 WHERE id = ANY($1);",
                problematic_ids
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
        print(f"❌ Error while fetching problematic questions: {e}")
        return []
    
async def get_top_documents_fts(query_text: str, limit: int = 10) -> list:
    return search_fts(query_text, limit=limit)
    

