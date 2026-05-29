import pandas as pd
import requests
from striprtf.striprtf import rtf_to_text

url = pd.read_csv("documents_structured.csv", nrows=1).iloc[0]["doc_url"]
raw_rtf = requests.get(url).text

clean_text = rtf_to_text(raw_rtf)

with open("clean_document.txt", "w", encoding="utf-8") as f:
    f.write(clean_text)

print(clean_text)