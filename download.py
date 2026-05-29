import os
import csv
import asyncio
import httpx

# Import your custom modules
from db_connection import init_db, get_pool, close_db
from services import process_row

CSV_FILE_PATH = "data_2025.csv"

async def download_and_save():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[ERROR] File {CSV_FILE_PATH} not found! Please check the path.")
        return

    # Step 1: Initialize the database pool
    print("Step 1: Initializing database pool...")
    try:
        await init_db()
        pool = get_pool()
    except Exception as e:
        print(f"[CRITICAL ERROR] Could not initialize DB pool: {e}")
        return

    # Configuration for batching
    limit = 1000
    batch_size = 20  
    count = 0
    current_batch = []

    print(f"\nStep 2: Starting pipeline in batches of {batch_size}...")
    
    # Step 2: Open HTTP client and read CSV file row by row
    async with httpx.AsyncClient(timeout=15.0) as client:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if count >= limit:
                    break

                current_batch.append(row)

                # Process batch when it reaches the max size or the final limit
                if len(current_batch) == batch_size or (count + len(current_batch) >= limit):
                    
                    # Creating concurrent tasks using imported service function
                    tasks = [process_row(r, client, pool) for r in current_batch]
                    results = await asyncio.gather(*tasks)
                    
                    # Calculate progress
                    successful_inserts = sum(1 for res in results if res is True)
                    count += successful_inserts
                    
                    print(f"Progress: {count}/{limit} documents successfully saved...")
                    current_batch = []

    # Step 3: Gracefully close the pool when done
    print("\nStep 3: Closing database pool...")
    await close_db()
    print(f"\n[DONE] Successfully saved {count} full court cases to the database.")


if __name__ == "__main__":
    asyncio.run(download_and_save())