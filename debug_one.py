import asyncio
import httpx
from datetime import datetime
from striprtf.striprtf import rtf_to_text
from db_connection import init_db, get_pool, close_db

async def debug_missing_row():
    await init_db()
    pool = get_pool()
    
    # 1. Fetch existing IDs
    print("[1/4] Fetching IDs from database...")
    rows = await pool.fetch("SELECT doc_id FROM documents;")
    db_ids = {r['doc_id'] for r in rows}
    
    # 2. Find the first missing row from CSV
    print("[2/4] Finding the first missing row in CSV...")
    target_row = None
    import csv
    with open("data_2025.csv", mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('doc_id') not in db_ids:
                target_row = row
                break
                
    if not target_row:
        print("[INFO] No missing rows found!")
        await close_db()
        return

    print(f"\n[3/4] Target row found!")
    print(f"-> doc_id: {target_row.get('doc_id')}")
    print(f"-> doc_url: {target_row.get('doc_url')}")
    
    # 3. Live debug of process_row logic for this specific item
    print("\n[4/4] Starting live analysis...")
    url = target_row.get('doc_url')
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            print(f"Sending HTTP GET request to URL...")
            response = await client.get(url)
            print(f"Response Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[REASON] Stopped because status code is not 200!")
                await close_db()
                return
                
            print("Decoding RTF content...")
            rtf_content = response.content.decode('utf-8', errors='ignore')
            print(f"Raw content length: {len(rtf_content)} characters")
            
            print("Converting RTF to plain text...")
            plain_text = rtf_to_text(rtf_content).strip()
            print(f"Clean text length: {len(plain_text)} characters")
            
            if not plain_text:
                print("[REASON] Stopped because plain_text is empty after RTF conversion!")
                # Let's print a small piece of raw content to see what's inside
                print(f"First 200 chars of raw content: {repr(rtf_content[:200])}")
                await close_db()
                return
                
            print("Checking PostgreSQL insertion manually...")
            # If we reached this point, let's see if INSERT actually happens or fails silently
            print("Data is valid. If it wasn't saved before, it might be due to global batch errors.")
            
        except Exception as e:
            print(f"[EXCEPTION CAUGHT] {e}")

    await close_db()

if __name__ == "__main__":
    asyncio.run(debug_missing_row())