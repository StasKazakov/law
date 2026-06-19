import requests
import asyncio
from utils.db_connection import init_db, get_pool, close_db
from utils.db_handlers import fetch_chunks_without_embeddings
from config import VECTOR_COLUMN

url = "http://localhost:8000/v1/embeddings"

async def get_chanck():
    await init_db()
    pool = get_pool()
    rows = await fetch_chunks_without_embeddings(pool, VECTOR_COLUMN, 1)
    return rows[0]["chunk_text"]
    

chanck = asyncio.run(get_chanck())

print(chanck)

payload = {"input": chanck }

try:
    print(f"Отправка тестового запроса на {url}...")
    response = requests.post(url, json=payload, timeout=30)
    print("Статус ответа сервера:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        embedding = data["data"][0]["embedding"]
        print("\nПобеда! Сервер вернул вектор.")
        print("Размерность эмбеддинга:", len(embedding))
        print("Первые 5 значений вектора:", embedding[:5])
    else:
        print("Сервер ответил ошибкой:", response.text)
except Exception as e:
    print("\nНе удалось подключиться к серверу.")
    print("Проверь, правильный ли внешний порт указан из панели Vast.ai.")
    print("Детали ошибки сети:", e)