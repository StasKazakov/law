import os
import csv
import asyncio
import httpx

# Import your existing connection pool helpers and row processor
from utils.db_connection import init_db, get_pool, close_db
from services import process_row

CSV_FILE_PATH = "data_2025.csv"
BATCH_SIZE = 20

def get_total_rows(file_path: str) -> int:
    """
    Quickly counts total rows in CSV to estimate accurate progress.
    """
    print("[INFO] Counting total rows in CSV file...")
    with open(file_path, mode='rb') as f:
        return sum(1 for _ in f) - 1

async def run_updater():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[ERROR] CSV file not found at: {CSV_FILE_PATH}")
        return

    # Step 1: Initialize database connection pool
    print("[DB] Initializing connection pool...")
    try:
        await init_db()
        pool = get_pool()
    except Exception as e:
        print(f"[CRITICAL ERROR] DB pool initialization failed: {e}")
        return

    # Step 2: Fetch already existing doc_ids from the database
    print("[DB] Fetching existing doc_ids to build cache...")
    try:
        rows = await pool.fetch("SELECT doc_id FROM documents;")
        processed_ids = {r['doc_id'] for r in rows}
        print(f"[INFO] Successfully cached {len(processed_ids)} existing IDs from DB.")
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to fetch existing IDs: {e}")
        await close_db()
        return

    # Step 3: Get total rows for tracking progress percentage
    try:
        total_rows = get_total_rows(CSV_FILE_PATH)
    except Exception:
        total_rows = 0

    current_lines_read = 0
    new_saved_count = 0
    current_batch = []

    print(f"\n[START] Processing CSV in batches of {BATCH_SIZE} unique missing rows...")

    # Step 4: Open HTTP client and read CSV sequentially
    async with httpx.AsyncClient(timeout=15.0) as client:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                current_lines_read += 1
                doc_id = row.get('doc_id')

                # RESUME LOGIC: Meticulously skip what is already in DB
                if doc_id in processed_ids:
                    continue

                # Add missing row to the current batch
                current_batch.append(row)

                # Execute batch processing immediately when it hits BATCH_SIZE
                if len(current_batch) == BATCH_SIZE:
                    tasks = [process_row(r, client, pool) for r in current_batch]
                    results = await asyncio.gather(*tasks)
                    
                    # Count how many rows returned True (successfully saved)
                    success_count = sum(1 for res in results if res is True)
                    new_saved_count += success_count
                    
                    # Clear the batch for the next round
                    current_batch = []
                    
                    # Print real-time batch execution stats
                    pct = (current_lines_read / total_rows * 100) if total_rows > 0 else 0
                    print(f"Batch processed! CSV Line: {current_lines_read}/{total_rows} ({pct:.2f}%) | "
                          f"Saved in this batch: {success_count} | Total newly saved: {new_saved_count}")

            # Step 5: Flush remaining rows that didn't form a full batch of 20
            if current_batch:
                print(f"\n[INFO] Flushing final remaining batch of {len(current_batch)} rows...")
                tasks = [process_row(r, client, pool) for r in current_batch]
                results = await asyncio.gather(*tasks)
                
                success_count = sum(1 for res in results if res is True)
                new_saved_count += success_count

    # Step 6: Close pool safely
    print("\n[DB] Closing database pool...")
    await close_db()
    print(f"[DONE] Updater finished. Total new documents safely stored in this run: {new_saved_count}")


if __name__ == "__main__":
    asyncio.run(run_updater())