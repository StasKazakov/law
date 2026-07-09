GEMINI_RERANK_PROMPT_TEMPLATE = """
You are an expert legal retriever. Your task is to rerank the following documents based on their relevance to the user's query.
Analyze the query and the full text of each document. Rank them from most relevant to least relevant.

Return a JSON object containing exactly one key "reranked_ids", which holds an ordered list of the top {top_n} most relevant Document IDs.
Do not include any thinking process, markdown formatting inside the JSON, or text explanations.

User Query: {query}

Documents to rank:
{documents_payload}
"""