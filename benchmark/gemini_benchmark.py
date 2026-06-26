import asyncio
from utils.db_connection import init_db, close_db
from benchmark.functions import (
    fetching_questions, 
    get_gemini_embedding, 
    get_top_10_documents, 
    calculate_mrr_score,
    save_benchmark_result
)

async def main():
    await init_db()
    
    try:
        questions = await fetching_questions()
        total_questions = len(questions)
        
        if total_questions == 0:
            print("❌ No questions found in the database.")
            return
            
        total_mrr_score = 0.0
        print(f"Starting benchmark loop for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = q['target_document_id']
            
            embeddings = await get_gemini_embedding(q['text'])
            top_documents = await get_top_10_documents(embeddings)
            
            score = calculate_mrr_score(top_documents, target_id)
            total_mrr_score += score
            
            print(f"[{index}/{total_questions}] Question ID {q['id']}: Score = {score:.4f}")
            
        final_mrr = round(total_mrr_score / total_questions, 2)
        print(f"📊 Final Mean MRR for Gemini (chunk 256): {final_mrr:.2f}")
        
        await save_benchmark_result(final_mrr)
        print("✅ Final result successfully saved to 'benchmark' table.")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())