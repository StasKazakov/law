from utils.db_connection import get_pool
# Get ONLY problematic questions from database
async def fetching_problematic_questions():
    try:
        pool = get_pool()
        problematic_ids = [2, 7, 9, 14, 15, 16, 17]
        
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