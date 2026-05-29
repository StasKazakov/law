import os
import pandas as pd
import requests
from striprtf.striprtf import rtf_to_text
from concurrent.futures import ThreadPoolExecutor
import time

input_file = "documents_structured.csv"
output_folder = "docs"
num_rows_to_test = 1000
max_workers = 20  

os.makedirs(output_folder, exist_ok=True)

def download_and_clean_document(row):
    doc_id = row["doc_id"]
    url = row["doc_url"]
    
    if pd.isna(url):
        return
        
    file_path = os.path.join(output_folder, f"{doc_id}.txt")
    
    if os.path.exists(file_path):
        return

    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            clean_text = rtf_to_text(response.text)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(clean_text)
            print(f"[SUCCESS] Saved: {doc_id}.txt")
        else:
            print(f"[ERROR] Failed {doc_id} with status code: {response.status_code}")
            
    except Exception as e:
        print(f"[EXCEPTION] Error downloading {doc_id}: {e}")

if __name__ == "__main__":
    print(f"Loading first {num_rows_to_test} rows from CSV...")
    df = pd.read_csv(input_file, nrows=num_rows_to_test)
    records = df.to_dict(orient="records")
    
    print(f"Starting download of {len(records)} files using {max_workers} threads...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(download_and_clean_document, records)
        
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "="*40)
    print(f"Test finished in {total_time:.2f} seconds.")
    print(f"Average speed: {total_time / len(records):.4f} seconds per document.")
    print(f"Estimated time for 8 million docs at this speed: {(total_time / len(records)) * 8000000 / 3600:.2f} hours.")
    print("="*40)