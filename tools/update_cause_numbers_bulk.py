import asyncio
import csv
from tools.db_connection import init_db, get_pool, close_db

BATCH_SIZE = 50000  # Update 50k rows at a time to prevent blocking

async def update_cause_numbers_in_batches(csv_file_path: str):
    print("Connecting to DB...")
    await init_db()
    pool = get_pool()

    print(f"Reading CSV file: {csv_file_path}...")
    
    batch = []
    total_processed = 0

    with open(csv_file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            doc_id = row.get('doc_id')
            cause_num = row.get('cause_num')
            
            # Check both fields and ensure cause_num is not empty
            if doc_id and cause_num and cause_num.strip():
                batch.append((doc_id, cause_num.strip()))
            
            # When the batch is full, write it to the DB
            if len(batch) >= BATCH_SIZE:
                await execute_batch_update(pool, batch)
                total_processed += len(batch)
                print(f"[PROGRESS] Successfully updated {total_processed} rows with cause numbers...")
                batch = [] # Clear the batch

        # Process remaining rows
        if batch:
            await execute_batch_update(pool, batch)
            total_processed += len(batch)
            print(f"[PROGRESS] Finished! Total updated rows: {total_processed}")

    # Close DB connection pool at the end
    await close_db()

async def execute_batch_update(pool, batch_data):
    async with pool.acquire() as conn:
        # Transaction only for the current batch
        async with conn.transaction():
            # Created a temp table with VARCHAR(255) to prevent truncation errors
            await conn.execute("""
                CREATE TEMP TABLE temp_cause_batch (
                    doc_id VARCHAR(50),
                    cause_num VARCHAR(255)
                ) ON COMMIT DROP;
            """)

            # Fast bulk insert into the temp table
            await conn.executemany(
                "INSERT INTO temp_cause_batch (doc_id, cause_num) VALUES ($1, $2);",
                batch_data
            )

            # Update the main production table
            await conn.execute("""
                UPDATE doc_2025 t
                SET cause_num = m.cause_num
                FROM temp_cause_batch m
                WHERE t.doc_id = m.doc_id;
            """)

if __name__ == "__main__":
    # Ensure the path to your big CSV file is correct
    asyncio.run(update_cause_numbers_in_batches("data/data_2025.csv"))