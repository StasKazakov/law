import asyncio
from config import VECTOR_COLUMN
from utils.db_connection import init_db, close_db, get_pool
from rerank.functions import rerank_documents_local
from benchmark.functions import (
    fetching_questions, 
    get_qwen_embedding, 
    get_top_documents, 
    calculate_linear_rank_score,
    fetch_best_chunks_for_documents,
    fetch_full_documents
)

async def main():
    await init_db()
    pool = get_pool()
    
    try:
        questions = await fetching_questions()
        total_questions = len(questions)
        
        if total_questions == 0:
            print("❌ No questions found in the database.")
            return
            
        total_score = 0.0
        print(f"Starting Diagnostic Loop for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = int(q['target_document_id'])
            question_text = q['text']
            
            embeddings = await get_qwen_embedding(question_text)
            top_doc_ids = await get_top_documents(embeddings, vector_column=VECTOR_COLUMN, limit=20)
            full_texts = await fetch_full_documents(pool, top_doc_ids)
            print(f"Full texts:\n{full_texts}")
            
            if top_doc_ids and isinstance(top_doc_ids[0], (tuple, list)):
                clean_ids = [int(doc[0]) for doc in top_doc_ids]
            else:
                clean_ids = [int(doc) for doc in top_doc_ids]

            was_found_initially = target_id in clean_ids
            initial_pos = clean_ids.index(target_id) + 1 if was_found_initially else -1

            doc_texts = await fetch_best_chunks_for_documents(
                pool, clean_ids, embeddings, VECTOR_COLUMN
            )
            
            if not doc_texts or len(doc_texts) != len(clean_ids):
                print(f"⚠️ Warning: Mismatch or no chunks found for IDs: {clean_ids}")
                score = calculate_linear_rank_score(clean_ids, target_id)
                total_score += score
                continue

            reranked_results = rerank_documents_local(query=question_text, documents=doc_texts, top_n=10)
            
            reranked_ids = []
            for item in reranked_results:
                original_index = item['index']
                reranked_ids.append(clean_ids[original_index])
            
            was_found_after = target_id in reranked_ids
            final_pos = reranked_ids.index(target_id) + 1 if was_found_after else -1

            score = calculate_linear_rank_score(reranked_ids, target_id)
            total_score += score
            
            print(f"\n[Question {index}/{total_questions}] ID: {q['id']}")
            print(f"  Target Doc ID: {target_id}")
            print(f"  Captured by Qwen (Top 20): {'✅ YES' if was_found_initially else '❌ NO'} (Initial Pos: {initial_pos})")
            print(f"  Captured by BGE Reranker (Top 10): {'✅ YES' if was_found_after else '❌ NO'} (Final Pos: {final_pos})")
            print(f"  Score: {score:.2f}")
            
        final_score = round(total_score / total_questions, 2)
        print(f"\n📊 Final Reranked Score for Qwen + BGE Reranker v2 M3 Local: {final_score:.2f}")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())