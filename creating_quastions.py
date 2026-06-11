import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from tools.functions import get_eval_documents, generate_legal_question
from tools.db_connection import init_db, close_db

async def main():
    # Initialize connection pool
    pool = await init_db()
    
    # Fetch all rows where question IS NULL
    docs = await get_eval_documents(pool)
    
    print(f"[INFO] Found {len(docs)} documents to process.")
    
    # Iterate through each document with index for tracking
    for index, doc in enumerate(docs, start=1):
        # Using doc_id as the primary identifier instead of db_id to avoid NULL issues
        doc_id = doc['doc_id']
        doc_text = doc['text']
        
        print(f"[{index}/{len(docs)}] 🔧 Processing doc_id: {doc_id} ...")
        
        # Generate question using Gemini
        result_id, question = generate_legal_question(doc_id, doc_text)
        
        if question:
            
            try:
            
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute(
                            """
                            UPDATE doc_eval_100 
                            SET question = $1 
                            WHERE doc_id = $2;
                            """, 
                            question, 
                            doc_id
                        )
                print(f"✅ Saved question for doc_{doc_id}")
            except Exception as db_err:
                print(f"❌ Database error while saving doc_{doc_id}: {db_err}")
        else:
            print(f"⚠️ Empty question generated for doc_{doc_id}")
            
        # Cooldown to perfectly respect the 15 RPM free tier rate limits
        await asyncio.sleep(5.0)

    # Cleanly close connection pool when done
    print("[INFO] Processing finished. Closing database connection...")
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())

