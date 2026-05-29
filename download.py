import os
import csv
import asyncio
from datetime import datetime
import httpx
from striprtf.striprtf import rtf_to_text

# Import connection pool functions from your db.py
from db_connection import init_db, get_pool, close_db

CSV_FILE_PATH = "data_2025.csv"

async def download_and_save():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[ERROR] File {CSV_FILE_PATH} not found! Please check the path.")
        return

    # Step 1: Initialize the database pool from db.py
    print("Step 1: Initializing database pool...")
    try:
        await init_db()
        pool = get_pool()
    except Exception as e:
        print(f"[CRITICAL ERROR] Could not initialize DB pool: {e}")
        return

    limit = 1000
    count = 0

    # Step 2: Initialize async HTTP client for downloading files
    print("\nStep 2: Starting pipeline for the first 1000 documents...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if count >= limit:
                    break

                url = row.get('doc_url')
                doc_id = row.get('doc_id')
                court_code = row.get('court_code')
                
                if not url:
                    continue

                # Parse the adjudication date safely
                raw_date = row.get('adjudication_date')
                judgment_date = None
                if raw_date:
                    try:
                        date_str = raw_date.split(' ')[0]
                        judgment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except Exception:
                        pass  # If date format is corrupted, leave it as None

                try:
                    # 1. Download the RTF file via HTTP
                    response = await client.get(url)
                    if response.status_code != 200:
                        print(f"[DOWNLOAD ERROR] Status {response.status_code} for ID {doc_id}")
                        continue

                    # 2. Extract and decode RTF content
                    rtf_content = response.content.decode('utf-8', errors='ignore')
                    plain_text = rtf_to_text(rtf_content).strip()

                    if not plain_text:
                        print(f"[PARSE WARNING] Empty text extracted for ID {doc_id}")
                        continue

                    # 3. CRITICAL CLEANUP: Remove PostgreSQL-breaking Null-bytes (\x00)
                    plain_text = plain_text.replace('\x00', '')
                    if doc_id:
                        doc_id = doc_id.replace('\x00', '')
                    if court_code:
                        court_code = court_code.replace('\x00', '')

                    # 4. Insert into public.documents using the pool
                    # ON CONFLICT (doc_id) DO NOTHING handles duplicates automatically
                    await pool.execute(
                        """
                        INSERT INTO documents (doc_id, doc_url, court_code, judgment_date, clean_text)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (doc_id) DO NOTHING;
                        """,
                        doc_id,
                        url,
                        court_code,
                        judgment_date,
                        plain_text
                    )

                    count += 1
                    if count % 10 == 0:
                        print(f"Successfully processed and saved {count}/{limit} documents...")

                except Exception as e:
                    print(f"[ERROR] Failed processing row {doc_id}: {e}")
                    continue

    # Step 3: Gracefully close the pool when done
    print("\nStep 3: Closing database pool...")
    await close_db()
    print(f"\n[DONE] Finished! Successfully saved {count} full court cases to the database.")

if __name__ == "__main__":
    # Start the async loop
    asyncio.run(download_and_save())