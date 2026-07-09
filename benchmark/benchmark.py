import asyncio
from utils.db_connection import init_db, close_db, get_pool
from benchmark.functions import (
    fetching_questions, 
    get_qwen_embedding, 
    calculate_linear_rank_score,
)
from hybrid_search.search import get_hybrid_search_results

async def main():
    await init_db()
    
    try:
        questions = await fetching_questions()
        total_questions = len(questions)
        
        if total_questions == 0:
            print("❌ No questions found in the database.")
            return
            
        total_score = 0.0
        print(f"Starting Clean Hybrid Search Baseline (Top-10 Docs) for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = str(q['target_document_id'])
            question_text = q['text']
            
            embeddings = await get_qwen_embedding(question_text)
            
            hybrid_results = await get_hybrid_search_results(
                query_text=question_text,
                query_embedding=embeddings,
                limit=10
            )
            
            unique_doc_ids = [str(doc['doc_id']) for doc in hybrid_results]
            
            print(f"\n[Question {index}/{total_questions}] ID: {q['id']}")
            print(f"  Top 10 Unique Doc IDs from Hybrid Search: {unique_doc_ids}")
            
            was_found = target_id in unique_doc_ids
            position = unique_doc_ids.index(target_id) + 1 if was_found else -1
            
            score = calculate_linear_rank_score(unique_doc_ids, target_id)
            total_score += score
            
            print(f"  Target Doc ID: {target_id}")
            print(f"  Captured by Hybrid Search (Top 10): {'✅ YES' if was_found else '❌ NO'} (Pos: {position})")
            print(f"  Score: {score:.2f}")
            
        final_score = round(total_score / total_questions, 2)
        print(f"\n📊 Final Baseline Score for Pure Hybrid Search (Qwen + FTS Top-10): {final_score:.2f}")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())