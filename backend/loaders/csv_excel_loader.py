import pandas as pd

def load_csv_excel(path: str) -> str:
    df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
    return df.to_string(index=False)
