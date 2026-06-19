import requests
import time

url = "http://localhost:8000/v1/embeddings"
payload = {"input": "тест", "model": "Mira190/Euler-Legal-Embedding-V1"}

for i in range(3):
    start = time.time()
    response = requests.post(url, json=payload, timeout=120)
    elapsed = time.time() - start
    print(f"Запрос {i+1}: {elapsed:.2f} сек, статус: {response.status_code}")