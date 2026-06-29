from datetime import datetime
import httpx
from striprtf.striprtf import rtf_to_text

async def process_row(row: dict, client: httpx.AsyncClient, pool) -> bool:
    
    url = row.get('doc_url')
    doc_id = row.get('doc_id')
    court_code = row.get('court_code')
    
    if not url:
        return False

    # Safely parse the adjudication date
    raw_date = row.get('adjudication_date')
    judgment_date = None
    if raw_date:
        try:
            date_str = raw_date.split(' ')[0]
            judgment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            pass  

    try:
        response = await client.get(url)
        if response.status_code != 200:
            return False

        rtf_content = response.content.decode('utf-8', errors='ignore')
        plain_text = rtf_to_text(rtf_content).strip()

        if not plain_text:
            return False

        plain_text = plain_text.replace('\x00', '')
        if doc_id: 
            doc_id = doc_id.replace('\x00', '')
        if court_code: 
            court_code = court_code.replace('\x00', '')

        await pool.execute(
            """
            INSERT INTO documents (doc_id, doc_url, court_code, judgment_date, clean_text)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (doc_id) DO NOTHING;
            """,
            doc_id,
            url,
            court_code,
            judgment_date,
            plain_text
        )
        return True

    except Exception as e:
        print(f"[ROW ERROR] Failed to process ID {doc_id}: {e}")
        return False