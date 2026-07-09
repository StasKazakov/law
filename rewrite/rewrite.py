import asyncio
from utils.db_connection import init_db, close_db
from rewrite.functions import fetching_problematic_questions

async def main():
    
    await init_db()
    
    try:
        questions = await fetching_problematic_questions()
        print(questions)

    except Exception as e:
        print(f"❌ Error while fetching problematic questions: {e}")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())