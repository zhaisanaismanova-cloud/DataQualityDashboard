
import pandas as pd
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent / "data" / "customer_orders.csv"


df = pd.read_csv(DATA_FILE)

print("\n=== CUSTOMER ORDERS: DATA PREVIEW ===")
print(df.to_string(index=False))

print("\n=== DATASET SIZE ===")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

print("\n=== MISSING VALUES ===")
print(df.isnull().sum())

print("\n=== DUPLICATE ROWS ===")
print(f"Duplicate rows: {df.duplicated().sum()}")

print("\n=== COLUMN DATA TYPES ===")
print(df.dtypes)

print("\n=== NUMERIC SUMMARY ===")
print(df.describe())
