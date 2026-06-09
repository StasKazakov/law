from dotenv import load_dotenv
load_dotenv()

from tools.functions import get_eval_documents, generate_legal_question, save_generated_question
from tools.db_connection import init_db
from tools.gemini_connecton import gemini
import asyncio

async def main():
    pool = await init_db()
    docs = await get_eval_documents(pool)
    
    print(f"[INFO] Found {len(docs)} documents to process.")
    
    for doc in docs:
        db_id = doc['id']
        doc_id = doc['doc_id']
        doc_text = doc['text']
        
        print(f"Processing doc_id: {doc_id} ...")
        
        # Generate question using Gemini
        result_id, question = generate_legal_question(doc_id, doc_text)
        
        if question:
            # Save to the database
            await save_generated_question(pool, db_id, question)
            print(f"[SUCCESS] Saved question for doc_{doc_id}")
        else:
            print(f"[WARNING] Empty question generated for doc_{doc_id}")
            
        # Cooldown to respect free tier rate limits
        await asyncio.sleep(5.0)

if __name__ == "__main__":
    asyncio.run(main())
        


