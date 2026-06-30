import asyncio
from utils.db_connection import init_db, close_db
from benchmark.functions import (
    fetching_questions, 
    get_openai_embedding, 
    get_top_10_documents, 
    calculate_linear_rank_score,
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
            
        total_score = 0.0
        print(f"Starting OpenAI benchmark loop for {total_questions} questions...")
        
        for index, q in enumerate(questions, start=1):
            target_id = q['target_document_id']
            
            embeddings = await get_openai_embedding(q['text'])
            top_documents = await get_top_10_documents(embeddings, vector_column="openai_vector")
            
            score = calculate_linear_rank_score(top_documents, target_id)
            total_score += score
            
            print(f"[{index}/{total_questions}] Question ID {q['id']}: Score = {score:.2f}")
            
        final_score = round(total_score / total_questions, 2)
        print(f" Bars Final Score for OpenAI (chunk 1024): {final_score:.2f}")
        
        # Saving using the universal function
        await save_benchmark_result(final_score, model_column="openai", chunk_size="1536")
        print("✅ OpenAI result successfully saved to 'benchmark' table.")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())