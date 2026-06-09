import csv
from db_connection import init_db, get_pool, close_db

async def find_hidden_symbols():
    await init_db()
    pool = get_pool()
    
    print("Step 1: Fetching IDs from database...")
    rows = await pool.fetch("SELECT doc_id FROM documents;")
    db_ids = {r['doc_id'] for r in rows}
    print(f"[INFO] Loaded {len(db_ids)} IDs from database.")
    
    print("Step 2: Analyzing CSV file row by row...")
    with open("data_2025.csv", mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, 2): # Starts at line 2 (after header)
            doc_id = row.get('doc_id')
            
            # If this ID from CSV is NOT found in the database, 
            # let's look at it closely.
            if doc_id not in db_ids:
                print("\n=== Found a mismatch! ===")
                print(f"CSV Line number: {idx}")
                print(f"Raw doc_id value in Python: {repr(doc_id)}")
                
                # Let's check if it exists in DB without spaces/newlines
                cleaned_id = doc_id.strip()
                if cleaned_id in db_ids:
                    print(f"Status: This ID exists in DB as '{cleaned_id}', but CSV has hidden spaces/newlines!")
                else:
                    print("Status: This ID is truly missing from the database.")
                
                break # We just need 1 example to understand
                
    await close_db()

if __name__ == "__main__":
    import asyncio
    asyncio.run(find_hidden_symbols())