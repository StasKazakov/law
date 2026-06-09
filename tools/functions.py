import json
from tools.gemini_connecton import gemini
from dotenv import load_dotenv
from tools.prompts import QUESTION_GENERATION_PROMPT
import os

load_dotenv()

model=os.getenv("MODEL")


async def get_eval_documents(pool) -> list:
    """Get and return data from doc_eval_100 table"""
    query = """
        SELECT id, doc_id, text, justice_kind 
        FROM doc_eval_100 
        WHERE question IS NULL 
        ORDER BY id;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query)

def generate_legal_question(doc_id: str, document_text: str) -> tuple:
    """Send document text to Gemini and return a tuple of (doc_id, question) from JSON response"""
    response = gemini.models.generate_content(
        model=model,
        contents=f"Document ID: {doc_id}\n\nDocument Text:\n{document_text}",
        config={
            'system_instruction': QUESTION_GENERATION_PROMPT,
            'temperature': 0.4,
            'response_mime_type': 'application/json' 
        }
    )
    
    try:
        
        data = json.loads(response.text.strip())
        return data.get("doc_id"), data.get("question")
    except (json.JSONDecodeError, TypeError):
        
        return doc_id, None

async def save_generated_question(pool, db_id: int, question: str) -> None:
    """Update the doc_eval_100 table with the generated question by record id"""
    query = """
        UPDATE doc_eval_100 
        SET question = $1 
        WHERE id = $2;
    """
    async with pool.acquire() as conn:
        await conn.execute(query, question, db_id)