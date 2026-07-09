import os
from typing import List, Dict, Any
import httpx
import json
import asyncio
from rerank.prompt import GEMINI_RERANK_PROMPT_TEMPLATE
from utils.clients import gemini_client
import re

def rerank_documents(query: str, documents: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Reranks a list of retrieved documents against a query using Cohere Rerank 4 Pro via OpenRouter.
    Uses direct HTTP POST requests to match OpenRouter's custom /v1/rerank endpoint format.
    """
    if not documents:
        print("Warning: Empty document list provided for reranking.")
        return []

    
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    url = "https://openrouter.ai/api/v1/rerank"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "cohere/rerank-4-pro",
        "query": query,
        "documents": documents,
        "top_n": top_n
    }
    
    try:
        # Using synchronous HTTP client since main loop is calling it synchronously
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # OpenRouter standard format returns results inside 'results' key
            # Each item contains: {"index": int, "relevance_score": float}
            reranked_results = data.get("results", [])
            return reranked_results
            
    except Exception as e:
        print(f"Error during reranking process: {str(e)}")
        # Critical Fallback: if API fails, return documents in their original order
        return [{"index": i, "relevance_score": 0.0} for i in range(len(documents))]
    

def rerank_documents_local(query: str, documents: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
    if not documents:
        return []

    url = "http://localhost:1234/v1/embeddings"
    headers = {"Content-Type": "application/json"}
    model_name = "text-embedding-bge-reranker-v2-m3"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            # 1. Get embedding for the query
            query_payload = {
                "model": model_name,
                "input": query
            }
            query_response = client.post(url, headers=headers, json=query_payload)
            if query_response.status_code != 200:
                print(f"❌ [LOCAL RERANK] Query embedding failed: {query_response.status_code}")
                return []
            
            query_vector = query_response.json()["data"][0]["embedding"]
            
            # 2. Get embeddings for all candidate documents in one batch
            doc_payload = {
                "model": model_name,
                "input": documents
            }
            doc_response = client.post(url, headers=headers, json=doc_payload)
            if doc_response.status_code != 200:
                print(f"❌ [LOCAL RERANK] Docs embedding failed: {doc_response.status_code}")
                return []
                
            docs_data = doc_response.json()["data"]
            
            # 3. Calculate Cosine Similarity (dot product for normalized vectors)
            scores = []
            for i, item in enumerate(docs_data):
                doc_vector = item["embedding"]
                
                # Math: dot product of two normalized vectors equals cosine similarity
                dot_product = sum(q * d for q, d in zip(query_vector, doc_vector))
                
                scores.append({
                    "index": i,
                    "relevance_score": float(dot_product)
                })
            
            # 4. Sort by actual mathematical similarity in descending order
            scores.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return scores[:top_n]
            
    except Exception as e:
        print(f"\n❌ [LOCAL RERANK EXCEPTION] Connection or calculation failed: {str(e)}")
        return []
    
async def rerank_documents_gemini(query: str, documents_map: Dict[int, str], top_n: int = 10) -> List[int]:
    if not documents_map:
        return []

    docs_input = []
    for doc_id, text in documents_map.items():
        truncated_text = text[:5000].replace("\n", " ")
        docs_input.append(f"ID: {doc_id}\nTEXT: {truncated_text}")

    documents_payload = "\n\n".join(docs_input)

    prompt = GEMINI_RERANK_PROMPT_TEMPLATE.format(
        top_n=top_n,
        query=query,
        documents_payload=documents_payload
    )

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gemini_client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0
                }
            )
        )
        
        data = json.loads(response.text)
        raw_ids = data.get("reranked_ids", [])
        
        reranked_ids = []
        for item in raw_ids:
            digits = re.sub(r"\D", "", str(item))
            if digits:
                reranked_ids.append(int(digits))
        
        valid_ids = [d_id for d_id in reranked_ids if d_id in documents_map]
        
        if not valid_ids:
            return list(documents_map.keys())[:top_n]
            
        return valid_ids[:top_n]

    except Exception as e:
        print(f"❌ Error during Gemini reranking: {str(e)}")
        return list(documents_map.keys())[:top_n]