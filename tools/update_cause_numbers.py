import asyncio
import pandas as pd
from utils.db_connection import init_db

# Укажи правильный путь к твоему CSV-файлу с метаданными
PATH_TO_CSV = "data/data_2025.csv"

async def update_cause_numbers():
    pool = await init_db()
    
    # 1. Забираем doc_id из нашей сотни
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT doc_id FROM doc_eval_100;")
    
    if not rows:
        print("[WARNING] Table doc_eval_100 is empty.")
        return
        
    eval_doc_ids = [str(row['doc_id']) for row in rows]
    print(f"[INFO] Found {len(eval_doc_ids)} docs in DB.")

    # 2. Загружаем ВЕСЬ CSV в память (с твоей ОЗУ это займет пару секунд)
    print(f"[INFO] Loading entire CSV into memory: {PATH_TO_CSV}")
    df = pd.read_csv(PATH_TO_CSV, dtype={'doc_id': str, 'cause_num': str})
    
    # 3. Фильтруем CSV прямо в памяти по нашей сотне ID
    print("[INFO] Filtering matching rows...")
    matched_df = df[df['doc_id'].isin(eval_doc_ids)].dropna(subset=['cause_num'])
    
    # 4. Записываем данные в базу одной быстрой транзакцией
    print(f"[INFO] Found {len(matched_df)} matches. Updating database...")
    async with pool.acquire() as conn:
        async with conn.transaction():
            for _, row in matched_df.iterrows():
                await conn.execute(
                    "UPDATE doc_eval_100 SET cause_num = $1 WHERE doc_id = $2;",
                    row['cause_num'], row['doc_id']
                )
                
    print("[SUCCESS] All cause numbers have been written to the database!")

if __name__ == "__main__":
    asyncio.run(update_cause_numbers())