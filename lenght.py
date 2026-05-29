import pandas as pd

input_file = "documents_structured.csv"
df = pd.read_csv(input_file, low_memory=False)
print("Done.")
print(len(df))