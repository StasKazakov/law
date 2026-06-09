import csv

CSV_FILE_PATH = "data/data_2025.csv"

def show_fifth_line():
    with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Read the header row (Line 1)
        header = next(reader)
        
        for idx, row in enumerate(reader, 2):
            if idx == 5:
                print("=== HEADER COLUMNS ===")
                print(header)
                print("\n=== ROW 5 DATA ===")
                print(row)
                
                print("\n=== COLUMN TO VALUE MAPPING ===")
                for col_name, value in zip(header, row):
                    print(f"{col_name}: {repr(value)}")
                break

if __name__ == "__main__":
    show_fifth_line()