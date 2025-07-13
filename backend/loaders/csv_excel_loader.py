# backend/loaders/csv_excel_loader.py

import pandas as pd
import os

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../temp_files'))

def load_building_data():
    return pd.read_csv(os.path.join(BASE_PATH, "building_data.csv"))

def load_unit_data():
    return pd.read_csv(os.path.join(BASE_PATH, "unit_data.csv"))
