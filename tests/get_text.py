from utils.db_connection import get_pool, init_db, close_db
import asyncio

async def get_text(doc_id: int) -> str:
    await init_db()
    pool = get_pool()
    query = """
        SELECT text
        FROM doc_sample_1k 
        WHERE doc_id = $1;
    """

    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, str(doc_id))
            print(rows[0]['text'])
            return rows[0]['text']
    except Exception as e:
        print(f"❌ Error while fetching text: {e}")
        return ""
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(get_text(126681254))
    
