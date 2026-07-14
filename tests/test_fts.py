import asyncio
from utils.db_connection import init_db, close_db, get_pool

async def main():
    await init_db()
    pool = get_pool()
    
    target_doc_id = '130476753'  # Проверим как строку и как число
    
    query = """
        SELECT id, doc_id, 
               (qwen_vector IS NOT NULL) as has_vector, 
               (fts_vector IS NOT NULL) as has_fts,
               pg_typeof(doc_id) as doc_id_type
        FROM chunks_512
        WHERE doc_id::text = $1
        LIMIT 5;
    """
    
    async with pool.acquire() as connection:
        rows = await connection.fetch(query, str(target_doc_id))
        
        if not rows:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Документа {target_doc_id} ВООБЩЕ НЕТ в таблице chunks_512!")
            # Давай проверим, сколько всего чанков в базе
            total = await connection.fetchval("SELECT COUNT(*) FROM chunks_512;")
            print(f"📊 Всего чанков в базе: {total}")
        else:
            print(f"✅ Документ {target_doc_id} найден!")
            print(f"   ℹ️ Тип поля doc_id в базе: {rows[0]['doc_id_type']}")
            for i, r in enumerate(rows):
                print(f"   📝 Чанк {i+1}: ID={r['id']}, Имеет вектор={r['has_vector']}, Имеет FTS={r['has_fts']}")
                
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())