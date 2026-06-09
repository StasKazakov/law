import asyncio
from tools.db_connection import get_total_documents_count, init_db, close_db


async def main():
    await init_db()
    await get_total_documents_count()
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())