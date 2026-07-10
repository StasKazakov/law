import asyncio
from utils.db_connection import init_db, close_db
from rewrite.functions import fetching_problematic_questions, rephrase_question
from benchmark.functions import new_get_top_documents, get_qwen_embedding
from config import VECTOR_COLUMN 

async def main():
    await init_db()
    
    try:
        questions = await fetching_problematic_questions()
        
        print(f"🚀 Starting benchmark on {len(questions)} problematic questions...")
        print("-" * 60)

        captured_count = 0
        total_questions = len(questions)

        for q in questions:
            q_dict = dict(q) if not isinstance(q, dict) else q
            question_id = q_dict.get("id")
            question_text = q_dict.get("text")
            rephrased_text = await rephrase_question(question_text)
            target_doc_id = q_dict.get("target_document_id")

            embedding = await get_qwen_embedding(rephrased_text) 

            unique_doc_ids = await new_get_top_documents(
                question_embedding=str(embedding),
                vector_column=VECTOR_COLUMN,
                limit=10
            )

            is_captured = target_doc_id in unique_doc_ids
            position = unique_doc_ids.index(target_doc_id) + 1 if is_captured else -1

            if is_captured:
                captured_count += 1
                status_str = f"✅ FIXED (Pos: {position})"
            else:
                status_str = "❌ STILL FAILED"

            print(f"[Q ID: {question_id}] Target Doc: {target_doc_id} -> {status_str}")

        accuracy = captured_count / total_questions
        print("-" * 60)
        print(f"📊 Problematic Subset Accuracy: {accuracy:.2f} ({captured_count}/{total_questions})")
        print("Goal: Push this number above 0.00 by tweaking chunks or using hybrid search!")

    except Exception as e:
        print(f"❌ Error during benchmarking: {e}")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())