import asyncio
from utils.db_connection import init_db, close_db
from config import VECTOR_COLUMN  
from benchmark.functions import (
    fetching_questions, 
    get_qwen_embedding, 
    calculate_linear_rank_score,
    get_top_documents,  
)

async def main():
    await init_db()
    
    try:
        questions = await fetching_questions()
        total_questions = len(questions)
        
        if total_questions == 0:
            print("❌ No questions found in the database.")
            return
            
        total_score = 0.0
        print(f"Starting Pure Vector Search Baseline (Top-10 Docs) for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = q['target_document_id']  
            question_text = q['text']
            
            embeddings = await get_qwen_embedding(question_text)
            
            unique_doc_ids = await get_top_documents(
                question_embedding=str(embeddings),
                vector_column=VECTOR_COLUMN,
                limit=10
            )
            
            print(f"\n❓ Question {index}/{total_questions} ID: {q['id']}")
            
            was_found = target_id in unique_doc_ids
            position = unique_doc_ids.index(target_id) + 1 if was_found else -1
            
            score = calculate_linear_rank_score(unique_doc_ids, target_id)
            total_score += score
            
            print(f"✅  Captured by Vector Search (Top 10): {'✅ YES' if was_found else '❌ NO'} (Pos: {position})")
            print(f"💯  Score: {score:.2f}")
            
        final_score = round(total_score / total_questions, 2)
        print(f"\n📊 Final Baseline Score for Pure Vector Search (Top-10): {final_score:.2f}")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())