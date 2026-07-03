import asyncio
from config import VECTOR_COLUMN
from utils.db_connection import init_db, close_db, get_pool
from rerank.functions import rerank_documents
from benchmark.functions import (
    fetching_questions, 
    get_qwen_embedding, 
    get_top_documents, 
    calculate_linear_rank_score,
    fetch_best_chunks_for_documents
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
        print(f"Starting Qwen + Cohere Rerank 4 Pro benchmark loop for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = q['target_document_id']
            question_text = q['text']
            
            # Step 1: Initial dense retrieval -> returns list of document IDs (ints)
            embeddings = await get_qwen_embedding(question_text)
            top_doc_ids = await get_top_documents(embeddings, vector_column=VECTOR_COLUMN, limit=30)
            
            # Safe flattening/casting to clean integers
            if top_doc_ids and isinstance(top_doc_ids[0], (tuple, list)):
                clean_ids = [int(doc[0]) for doc in top_doc_ids]
            else:
                clean_ids = [int(doc) for doc in top_doc_ids]

            # Step 2: Get the best chunk text for each document id
            doc_texts = await fetch_best_chunks_for_documents(
                pool, clean_ids, embeddings, VECTOR_COLUMN
            )
            
            if not doc_texts or len(doc_texts) != len(clean_ids):
                print(f"⚠️ Warning: Mismatch or no chunks found for IDs: {clean_ids}")
                # Fallback to standard vector score if fetching text failed
                score = calculate_linear_rank_score(clean_ids, target_id)
                total_score += score
                continue

            # Step 3: Rerank the chunk texts using Cohere Rerank 4 Pro
            reranked_results = rerank_documents(query=question_text, documents=doc_texts, top_n=10)
            
            # Step 4: Map the reranker's reordered indices back to document IDs
            reranked_ids = []
            for item in reranked_results:
                original_index = item['index']
                reranked_ids.append(clean_ids[original_index])
                
            # Step 5: Score the new reranked list of document IDs
            score = calculate_linear_rank_score(reranked_ids, target_id)
            total_score += score
            
            print(f"[{index}/{total_questions}] Question ID {q['id']}: Reranked Score = {score:.2f}")
            
        final_score = round(total_score / total_questions, 2)
        print(f"📊 Final Reranked Score for Qwen + Cohere Rerank 4 Pro: {final_score:.2f}")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())