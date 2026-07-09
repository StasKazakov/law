import asyncio
from utils.db_connection import init_db, close_db, get_pool
from benchmark.functions import (
    fetching_questions, 
    get_qwen_embedding, 
    calculate_linear_rank_score,
)

from config import VECTOR_COLUMN

async def get_top_documents(question_embedding: list, vector_column: str, limit: int = 10) -> tuple[list, list]:
    pool = get_pool()
    raw_limit = limit * 3
    
    search_query = f"""
        SELECT doc_id, 1 - ({VECTOR_COLUMN} <=> $1::vector) as similarity_score
        FROM chunks_512 
        ORDER BY {VECTOR_COLUMN} <=> $1::vector 
        LIMIT {raw_limit};
    """
    
    async with pool.acquire() as connection:
        rows = await connection.fetch(search_query, question_embedding)
        
        seen_docs = set()
        unique_doc_ids = []
        doc_scores = []
        
        for row in rows:
            doc_id = int(row['doc_id'])
            score = round(float(row['similarity_score']), 4)
            
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_doc_ids.append(doc_id)
                doc_scores.append(score)
                
            if len(unique_doc_ids) == limit:
                break
                
        return unique_doc_ids, doc_scores

async def main():
    await init_db()
    
    try:
        questions = await fetching_questions()
        total_questions = len(questions)
        
        if total_questions == 0:
            print("❌ No questions found in the database.")
            return
 
        
        print(f"Starting Clean Vector Search Baseline (Top-10 Docs) for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = int(q['target_document_id'])  # Приводим к int, так как функция теперь возвращает int
            question_text = q['text']
            
            embeddings = await get_qwen_embedding(question_text)
            
            unique_doc_ids, doc_scores = await get_top_documents(
                question_embedding=embeddings,
                vector_column=VECTOR_COLUMN,
                limit=10
            )
            
            print(f"\n[Question {index}/{total_questions}] ID: {q['id']}")
            print(f"  Top 10 Unique Doc IDs from Vector Search: {unique_doc_ids}")
            print(f"  Document Scores (Cosine Similarity): {doc_scores}")
            
            was_found = target_id in unique_doc_ids
            position = unique_doc_ids.index(target_id) + 1 if was_found else -1
            
            str_doc_ids = [str(did) for did in unique_doc_ids]
            hit_score = calculate_linear_rank_score(str_doc_ids, str(target_id))
            
            print(f"  Target Doc ID: {target_id}")
            print(f"  Captured by Vector Search (Top 10): {'✅ YES' if was_found else '❌ NO'} (Pos: {position})")
            print(f"  Question Hit Score: {hit_score:.2f}")
            
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())