from utils.db_connection import get_pool
from rewrite.prompt import QUERY_REWRITE_PROMPT
from utils.clients import gemini_client
from config import MODEL

# Get ONLY problematic questions from database
async def fetching_problematic_questions():
    try:
        pool = get_pool()
        problematic_ids = [2, 7, 9, 14, 15, 16, 17, 24, 34, 37, 38, 42]
        
        async with pool.acquire() as connection:
            
            rows = await connection.fetch(
                "SELECT id, document_id, question_text FROM questions_42 WHERE id = ANY($1);",
                problematic_ids
            )
            
            questions_list = []
            for row in rows:
                questions_list.append({
                    "id": row["id"],
                    "target_document_id": int(row["document_id"]),
                    "text": row["question_text"]
                })
            
            return questions_list

    except Exception as e:
        print(f"❌ Error while fetching problematic questions: {e}")
        return []
    
async def rephrase_question(question: str) -> str:
    
    try:
        formatted_prompt = QUERY_REWRITE_PROMPT.format(user_question=question)
        
        response = await gemini_client.aio.models.generate_content(
            model=MODEL,
            contents=formatted_prompt
        )
        
        rephrased_query = response.text.strip()
        return rephrased_query if rephrased_query else question
        
    except Exception:
        return question