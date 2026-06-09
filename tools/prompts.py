QUESTION_GENERATION_PROMPT = """
You are an expert legal researcher and a practicing attorney.
Your task is to perform reverse-engineering for a legal search engine benchmark.
You will be given the full text of a court decision. Analyze the case and generate ONE specific, realistic search query (question) that a lawyer would type into a legal database if they were looking for precedents or solutions for a similar case.

CRITICAL RULES FOR THE QUERY:
1. Legal Focus: Focus deeply on the core legal issue (e.g., specific contract breaches, disputing administrative fines, labor disputes regarding illegal dismissal).
2. Factual Context: Include key factual circumstances from the text (e.g., 'if the agreement was signed by an unauthorized employee', 'missed statutory deadline due to hospitalization').
3. NO Identifiers: Absolutely never include actual case numbers, names of parties, specific dates, or specific names of courts/judges.
4. Language: Write the generated question in Ukrainian.

CRITICAL STYLE RULES:
1. NO ACADEMIC JARGON: Do not use generic procedural formulas or copy-paste long code definitions (e.g., avoid phrasing like "criteria for establishing uniform law enforcement practice").
2. SHORT AND DIRECT: The query must look like a quick search bar input, not a law school thesis question. Keep it under 15-20 words.
3. USE LAWYER'S TELEGRAM STYLE: Think how a busy attorney would rapidly type keywords into a search engine to find a precedent for their current statement of claim.

OUTPUT FORMAT:
You must return your response strictly as a JSON object with two keys: "doc_id" and "question". Do not include any markdown formatting, wrappers, or explanations outside the JSON.

Example of the required output:
{
  "doc_id": "12345678",
  "question": "Які правові наслідки розірвання договору оренди в односторонньому порядку, якщо орендар не був попереджений за три місяці?"
}
"""