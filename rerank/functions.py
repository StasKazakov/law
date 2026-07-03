import os
from typing import List, Dict, Any
import httpx

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