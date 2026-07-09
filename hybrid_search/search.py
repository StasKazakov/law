from typing import List, Dict, Any
from utils.db_connection import get_pool

async def get_hybrid_search_results(
    query_text: str, 
    query_embedding: List[float], 
    limit: int = 10
) -> List[Dict[str, Any]]:
    sql_query = """
    WITH vector_search AS (
        SELECT id, doc_id, row_number() OVER (ORDER BY qwen_vector <=> $1::vector) as rank
        FROM chunks_512
        WHERE qwen_vector IS NOT NULL
        ORDER BY qwen_vector <=> $1::vector
        LIMIT 40
    ),
    text_search AS (
        -- websearch_to_tsquery намного мягче и не требует строгого AND для всех слов
        SELECT id, doc_id, row_number() OVER (ORDER BY ts_rank_cd(fts_vector, websearch_to_tsquery('ukrainian', $3)) DESC) as rank
        FROM chunks_512
        WHERE fts_vector @@ websearch_to_tsquery('ukrainian', $3)
        LIMIT 40
    ),
    combined_rrf AS (
        SELECT 
            COALESCE(v.doc_id, t.doc_id) as doc_id,
            -- Даем вектору полный вес (1.0), а тексту — поддерживающий (0.3), чтобы он лишь слегка двигал топ
            (COALESCE(1.0 / (60 + v.rank), 0.0) * 1.0) + 
            (COALESCE(1.0 / (60 + t.rank), 0.0) * 0.3) as rrf_score
        FROM vector_search v
        FULL OUTER JOIN text_search t ON v.id = t.id
    )
    SELECT 
        r.doc_id,
        MAX(r.rrf_score) as max_score
    FROM combined_rrf r
    GROUP BY r.doc_id
    ORDER BY max_score DESC
    LIMIT $2;
    """
    
    try:
        pool = get_pool()
        rows = await pool.fetch(sql_query, query_embedding, limit, query_text)
        
        return [{"doc_id": r["doc_id"], "rrf_score": float(r["max_score"])} for r in rows]
        
    except Exception as e:
        print(f"❌ Failed to execute calibrated hybrid search: {e}")
        return []