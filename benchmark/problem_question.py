import asyncio
from config import VECTOR_COLUMN
from utils.db_connection import init_db, close_db, get_pool
from rerank.functions import rerank_documents
from benchmark.functions import (
    fetching_questions, 
    get_qwen_embedding, 
    get_top_documents, 
    fetch_best_chunks_for_documents
)

async def debug_specific_question(target_q_id: int):
    await init_db()
    pool = get_pool()
    
    try:
        questions = await fetching_questions()
        # Ищем именно тот вопрос, который нам нужен
        q = next((item for item in questions if int(item['id']) == target_q_id), None)
        
        if not q:
            print(f"❌ Question with ID {target_q_id} not found.")
            return
            
        target_id = int(q['target_document_id'])
        question_text = q['text']
        
        print(f"=== DEBUGGING QUESTION ID: {target_q_id} ===")
        print(f"❓ Question Text: {question_text}\n")
        print(f"🎯 Target Document ID: {target_id}")
        
        embeddings = await get_qwen_embedding(question_text)
        # Ищем топ-50, как у тебя сейчас настроено
        top_doc_ids = await get_top_documents(embeddings, vector_column=VECTOR_COLUMN, limit=50)
        
        clean_ids = [int(doc[0]) if isinstance(doc, (tuple, list)) else int(doc) for doc in top_doc_ids]
        
        doc_texts = await fetch_best_chunks_for_documents(pool, clean_ids, embeddings, VECTOR_COLUMN)
        
        # Находим, какой текст соответствует нашему таргету
        target_text = None
        if target_id in clean_ids:
            target_idx = clean_ids.index(target_id)
            target_text = doc_texts[target_idx]
            print(f"   ↳ Position in Vector Search: {target_idx + 1}")
        else:
            print("   ↳ ❌ Not found in vector search top-50")
            return

        reranked_results = rerank_documents(query=question_text, documents=doc_texts, top_n=10)
        
        print("\n🏆 Top-3 Documents chosen by Cohere:")
        for i, item in enumerate(reranked_results[:3], start=1):
            orig_idx = item['index']
            print(f" {i}. Doc ID: {clean_ids[orig_idx]} (Score: {item.get('relevance_score', 'N/A')})")
            print(f"    Text snippet: {doc_texts[orig_idx][:300]}...\n")
            
        print("🎯 Target Document Text:")
        print(f"    {target_text[:600]}...\n")
        
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(debug_specific_question(13))