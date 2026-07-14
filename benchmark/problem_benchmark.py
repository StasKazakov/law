import asyncio
from benchmark.functions import fetching_problem_questions, get_qwen_embedding, get_top_documents, get_top_documents_fts
from utils.db_connection import init_db, close_db
from config import VECTOR_COLUMN


def reciprocal_rank_fusion(vector_results, fts_results, k=10, top_n=10):
    rrf_scores = {}
    
    for rank, doc in enumerate(vector_results, start=1):
        doc_id = str(doc)
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        
    for rank, doc in enumerate(fts_results, start=1):
        doc_id = str(doc)
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        
    sorted_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
    return [doc_id for doc_id, score in sorted_docs[:top_n]]


async def main():
    try:
        await init_db()
        questions = await fetching_problem_questions()
        for q in questions:
            target_id = str(q['target_document_id'])
            question_text = q['text']
            print(f"🎯 Target Document ID: {target_id}")
            
            embeddings = await get_qwen_embedding(question_text)
            
            vec_100 = await get_top_documents(embeddings, vector_column=VECTOR_COLUMN, limit=100)
            fts_100 = await get_top_documents_fts(question_text, limit=100)
            
            hybrid_top_10 = reciprocal_rank_fusion(vec_100, fts_100, k=10, top_n=10)
            print(f"🔝 Hybrid Top-10: {hybrid_top_10}")
            
            if target_id in hybrid_top_10:
                print(f"✅ Question {q['id']} was captured by hybrid search.")
            else:
                vec_str = [str(d) for d in vec_100]
                fts_str = [str(d) for d in fts_100]
                pos_vec = vec_str.index(target_id) + 1 if target_id in vec_str else '100+'
                pos_fts = fts_str.index(target_id) + 1 if target_id in fts_str else '100+'
                print(f"❌ Question {q['id']} was not captured by hybrid search.")
                print(f"  (Pos in Vec: {pos_vec}, Pos in FTS: {pos_fts})")
                
    except Exception as e:
        print(f"❌ Error while fetching problematic questions: {e}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())