# tests/diagnostic_rank.py
import asyncio
from benchmark.functions import fetching_problem_questions, get_qwen_embedding
from utils.db_connection import init_db, close_db, get_pool
from config import VECTOR_COLUMN


async def main():
    await init_db()
    pool = get_pool()
    questions = await fetching_problem_questions()

    print("📊 --- ЗАПУСК ДИАГНОСТИКИ ПОИСКА --- 📊\n")

    for q in questions:
        target_id = str(q['target_document_id'])
        question_text = q['text']
        print(f"❓ Вопрос {q['id']}: \"{question_text[:80]}...\"")
        print(f"🎯 Target ID: {target_id}")

        # 1. Векторный анализ
        embeddings = await get_qwen_embedding(question_text)
        vec_query = f"""
            SELECT position, distance
            FROM (
                SELECT doc_id, 
                       ({VECTOR_COLUMN} <=> $1) as distance,
                       ROW_NUMBER() OVER (ORDER BY {VECTOR_COLUMN} <=> $1) as position
                FROM chunks_512
            ) sub
            WHERE doc_id = $2
            ORDER BY position ASC
            LIMIT 1;
        """

        # 2. FTS анализ
        # Формируем поисковую строку FTS
        words = [w for w in question_text.lower().split() if len(w) > 3]
        fts_query_string = " | ".join(words)
        
        fts_query = """
            SELECT position, max_rank
            FROM (
                SELECT doc_id, 
                       MAX(ts_rank_cd(fts_vector, to_tsquery('ukrainian', $1))) as max_rank,
                       ROW_NUMBER() OVER (ORDER BY MAX(ts_rank_cd(fts_vector, to_tsquery('ukrainian', $1))) DESC) as position
                FROM chunks_512
                WHERE fts_vector @@ to_tsquery('ukrainian', $1)
                GROUP BY doc_id
            ) sub
            WHERE doc_id = $2;
        """

        async with pool.acquire() as connection:
            # Выполняем векторный замер
            vec_row = await connection.fetchrow(vec_query, embeddings, target_id)
            if vec_row:
                print(f"  🧠 Vector: Позиция в топе: #{vec_row['position']} (Расстояние: {vec_row['distance']:.4f})")
            else:
                print("  🧠 Vector: Документ вообще не найден в выдаче!")

            # Выполняем FTS замер
            fts_row = await connection.fetchrow(fts_query, fts_query_string, target_id)
            if fts_row:
                print(f"  🔎 FTS:    Позиция в топе: #{fts_row['position']} (Rank: {fts_row['max_rank']:.4f})")
            else:
                print("  🔎 FTS:    Документ не соответствует поисковому FTS-запросу вообще (0 совпадений слов)!")
        
        print("-" * 50)

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())