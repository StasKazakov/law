import os
import csv
import asyncio
import httpx

# Import your custom modules
from db_connection import init_db, get_pool, close_db
from services import process_row

CSV_FILE_PATH = "data_2025.csv"

def get_total_rows(file_path: str) -> int:
    """
    Quickly counts the total number of lines in the CSV file 
    to show an accurate global progress bar.
    """
    print("Counting total rows in CSV (this may take a few seconds)...")
    with open(file_path, mode='rb') as f:
        # Subtract 1 to account for the header row
        return sum(1 for _ in f) - 1

async def download_and_save():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[ERROR] File {CSV_FILE_PATH} not found! Please check the path.")
        return

    # Step 1: Get total rows for the progress counter
    try:
        total_rows = get_total_rows(CSV_FILE_PATH)
        print(f"[INFO] Total rows to process: {total_rows}")
    except Exception as e:
        print(f"[WARNING] Could not calculate total rows: {e}")
        total_rows = 0

    # Step 2: Initialize the database pool
    print("Step 2: Initializing database pool...")
    try:
        await init_db()
        pool = get_pool()
    except Exception as e:
        print(f"[CRITICAL ERROR] Could not initialize DB pool: {e}")
        return

    # Step 3: Fetch already processed document IDs from DB to allow resuming
    print("Step 3: Fetching already processed doc_ids from database...")
    try:
        rows = await pool.fetch("SELECT doc_id FROM documents;")
        processed_ids = {r['doc_id'] for r in rows}
        print(f"[INFO] Found {len(processed_ids)} already processed documents in DB. Resuming...")
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to fetch processed IDs: {e}")
        await close_db()
        return

    # Configuration for batching
    batch_size = 20  
    current_lines_processed = 0  # Global counter for positions in CSV
    new_saved_count = 0
    current_batch = []

    print(f"\nStep 4: Starting full pipeline in batches of {batch_size}...")
    
    # Step 4: Open HTTP client and process CSV file row by row
    async with httpx.AsyncClient(timeout=15.0) as client:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                current_lines_processed += 1
                doc_id = row.get('doc_id')

                # RESUME LOGIC: Skip row if it was already processed, but still count it in progress
                if doc_id in processed_ids:
                    # If batch isn't empty, but we hit skipped rows, we should still process the batch 
                    # if it happens to be full, or just move on.
                    continue

                # Add new row to the current batch
                current_batch.append(row)

                # Process batch when it reaches the max size
                if len(current_batch) == batch_size:
                    tasks = [process_row(r, client, pool) for r in current_batch]
                    results = await asyncio.gather(*tasks)
                    
                    new_saved_count += sum(1 for res in results if res is True)
                    current_batch = []
                    
                    # Calculate percentage
                    pct = (current_lines_processed / total_rows * 100) if total_rows > 0 else 0
                    print(f"Progress: {current_lines_processed}/{total_rows} ({pct:.2f}%) | Newly saved in this run: {new_saved_count}")

            # Process any remaining rows in the final batch after the loop ends
            if current_batch:
                tasks = [process_row(r, client, pool) for r in current_batch]
                results = await asyncio.gather(*tasks)
                new_saved_count += sum(1 for res in results if res is True)
                
                pct = (current_lines_processed / total_rows * 100) if total_rows > 0 else 0
                print(f"Progress: {current_lines_processed}/{total_rows} ({pct:.2f}%) | Newly saved in this run: {new_saved_count}")

    # Step 5: Gracefully close the pool when done
    print("\nStep 5: Closing database pool...")
    await close_db()
    print(f"\n[DONE] Pipeline finished. Processed {current_lines_processed} rows. Saved {new_saved_count} new docs.")


if __name__ == "__main__":
    asyncio.run(download_and_save())