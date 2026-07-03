import asyncio
import csv
from utils.db_connection import init_db, get_pool, close_db

TABLE_MAPPING = {
    '1.0': 'civil',
    '2.0': 'criminal',
    '3.0': 'commercial',
    '4.0': 'admin',
    '5.0': 'infraction'
}

BATCH_SIZE = 50000  # Update 50k rows at a time to prevent blocking

async def update_in_batches(csv_file_path: str):
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
            raw_kind = row.get('justice_kind')
            
            if doc_id and raw_kind:
                mapped_kind = TABLE_MAPPING.get(raw_kind, 'other')
                batch.append((doc_id, mapped_kind))
            
            # When the batch is full, write it to the DB
            if len(batch) >= BATCH_SIZE:
                await execute_batch_update(pool, batch)
                total_processed += len(batch)
                print(f"[PROGRESS] Successfully updated {total_processed} rows...")
                batch = [] # Clear the batch

        # Process remaining rows
        if batch:
            await execute_batch_update(pool, batch)
            total_processed += len(batch)
            print(f"[PROGRESS] Finished! Total updated rows: {total_processed}")

async def execute_batch_update(pool, batch_data):
    async with pool.acquire() as conn:
        # Transaction only for the current batch
        async with conn.transaction():
            await conn.execute("""
                CREATE TEMP TABLE temp_batch (
                    doc_id VARCHAR(50),
                    justice_kind VARCHAR(20)
                ) ON COMMIT DROP;
            """)

            await conn.executemany(
                "INSERT INTO temp_batch (doc_id, justice_kind) VALUES ($1, $2);",
                batch_data
            )

            await conn.execute("""
                UPDATE doc_2025 t
                SET justice_kind = m.justice_kind
                FROM temp_batch m
                WHERE t.doc_id = m.doc_id;
            """)

if __name__ == "__main__":
    asyncio.run(update_in_batches("data/data_2025.csv"))