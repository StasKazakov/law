import os
import asyncio
import pandas as pd
from utils.db_connection import init_db, get_pool, close_db 

FILE_PATH = os.path.join("data", "legal_benchmark.xlsx")
TABLE_NAME = "questions_42"

async def import_benchmark():
    try:
        await init_db()
        pool = get_pool()

        print(f"Reading Excel file from: {FILE_PATH}")
        df = pd.read_excel(FILE_PATH, sheet_name=0)

        # Preparing list of tuples for asyncpg executemany
        rows_to_insert = []
        for _, row in df.iterrows():
            rows_to_insert.append((
                int(row['Document ID']),
                str(row['Case Number (Cause Num)']),
                int(row['Court Code']),
                str(row['Justice Kind']),
                str(row['Generated Question']),
                str(row['Document URL'])
            ))

        query = f"""
            INSERT INTO {TABLE_NAME} (document_id, case_number, court_code, justice_kind, question_text, document_url)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (document_id) DO NOTHING;
        """

        print(f"Starting async insertion of {len(rows_to_insert)} rows into '{TABLE_NAME}'...")
        
        async with pool.acquire() as connection:
            await connection.executemany(query, rows_to_insert)

        print(f"Successfully imported rows into '{TABLE_NAME}' database table.")

    except Exception as e:
        print(f"Error during async import execution: {e}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(import_benchmark())