from tools.db_connection import lenght_table, init_db, close_db
import asyncio

async def main():
    await init_db()
    await lenght_table('doc_eval_100')
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
