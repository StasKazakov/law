import asyncio
import pandas as pd
from tools.db_connection import init_db

async def export_benchmark_to_excel():
    """Fetch successfully generated rows with cause_num and export to Excel file"""
    pool = await init_db()
    
    # 1. Добавили cause_num в SELECT и выставили удобный порядок колонок
    query = """
        SELECT doc_id, cause_num, court_code, justice_kind, question, doc_url
        FROM doc_eval_100
        WHERE question IS NOT NULL
        ORDER BY id;
    """
    
    print("Fetching data from the database...")
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        
    if not rows:
        print("[WARNING] No generated questions found in the database yet.")
        return

    data = [dict(row) for row in rows]
    df = pd.DataFrame(data)
    
    # 2. Обновили названия колонок (теперь их 6, строго по порядку из SELECT)
    df.columns = [
        "Document ID", 
        "Case Number (Cause Num)", 
        "Court Code", 
        "Justice Kind", 
        "Generated Question", 
        "Document URL"
    ]
    
    output_filename = "legal_benchmark_examples.xlsx"
    print(f"Exporting {len(df)} records to {output_filename}...")
    
    # Exporting using openpyxl engine
    df.to_excel(output_filename, index=False, engine='openpyxl')
    print("[SUCCESS] Excel file generated successfully!")

if __name__ == "__main__":
    asyncio.run(export_benchmark_to_excel())