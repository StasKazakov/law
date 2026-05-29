import pandas as pd

input_file = "documents_structured.csv"

print("Reading the entire file into RAM... Please wait.")
df = pd.read_csv(input_file, nrows=1, low_memory=False)
print("Done.")
print(df.T)
