import pandas as pd

CSV_FILE_PATH = "data/data_2025.csv"

def check_csv_uniqueness():
    print("Reading CSV columns (this might take a minute)...")
    
    try:
        # We read ONLY 'doc_id' and 'doc_url' columns to save RAM
        df = pd.read_csv(
            CSV_FILE_PATH, 
            usecols=['doc_id', 'doc_url'], 
            dtype={'doc_id': str, 'doc_url': str}
        )
        
        print("\n--- CSV Statistics ---")
        total_rows = len(df)
        print(f"Total rows in CSV (excluding header): {total_rows}")
        
        # 1. Count unique doc_ids
        unique_ids = df['doc_id'].nunique()
        print(f"Unique 'doc_id' count: {unique_ids}")
        
        # 2. Count unique doc_urls (as you requested)
        unique_urls = df['doc_url'].nunique()
        print(f"Unique 'doc_url' count: {unique_urls}")
        
        # 3. Check for exact duplicate rows within these two columns
        duplicate_rows = df.duplicated(subset=['doc_id']).sum()
        print(f"Total duplicate 'doc_id' entries found by Pandas: {duplicate_rows}")
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze CSV: {e}")

if __name__ == "__main__":
    check_csv_uniqueness()