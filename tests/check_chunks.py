import asyncio
from utils.db_connection import init_db, get_pool, close_db

async def verify_chunks():
    pool = get_pool()
    
    # 1. Проверяем общее количество и типы данных
    stats = await pool.fetchrow("""
        SELECT 
            COUNT(*) as total_chunks,
            COUNT(DISTINCT doc_id) as total_docs,
            COUNT(*) FILTER (WHERE embedding IS NULL) as empty_embeddings
        FROM doc_embeddings;
    """)
    
    print("--- ОБЩАЯ СТАТИСТИКА ---")
    print(f"Всего чанков в базе: {stats['total_chunks']}")
    print(f"Уникальных документов: {stats['total_docs']}")
    print(f"Чанков без векторов (NULL): {stats['empty_embeddings']}")
    
    # 2. Достаем один случайный документ со всеми его чанками для проверки структуры
    sample_doc = await pool.fetchrow("SELECT doc_id FROM doc_embeddings LIMIT 1;")
    if not sample_doc:
        print("База пуста.")
        return

    doc_id = sample_doc['doc_id']
    chunks = await pool.fetch("""
        SELECT chunk_index, chunk_text 
        FROM doc_embeddings 
        WHERE doc_id = $1 
        ORDER BY chunk_index;
    """, doc_id)
    
    print(f"\n--- ПРОВЕРКА СТРУКТУРЫ ДЛЯ DOC_ID: {doc_id} ---")
    print(f"Этот документ разбился на {len(chunks)} чанков.")
    
    for row in chunks:
        print(f"\n[ЧАНК №{row['chunk_index']}]")
        print("-" * 40)
        print(row['chunk_text'])
        print("-" * 40)

async def main():
    await init_db()
    try:
        await verify_chunks()
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())