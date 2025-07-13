import pandas as pd
from backend.loaders.csv_excel_loader import load_unit_data

class MatchingAgent:
    def __init__(self):
        self.units = load_unit_data()

    def find_matches(self, preferences: dict) -> list:
        df = self.units

        # Filter on price
        if "budget" in preferences:
            df = df[df['price'] <= preferences["budget"]]

        # Filter on location
        if "location" in preferences:
            df = df[df['location'].str.contains(preferences["location"], case=False)]

        matches = df.head(3).to_dict(orient="records")
        return matches
