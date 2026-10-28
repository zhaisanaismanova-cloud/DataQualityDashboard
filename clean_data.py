
import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "customer_orders.csv"


df = pd.read_csv(DATA_FILE)

print("=== STARTING DATA CLEANING ===")
print(f"Original rows: {len(df)}")


duplicate_count = int(df.duplicated().sum())
df = df.drop_duplicates().copy()


text_columns = ["customer_name", "email", "product"]

for column in text_columns:
    df[column] = df[column].astype("string").str.strip()


df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")


required_fields = [
    "order_id",
    "customer_name",
    "email",
    "order_date",
    "product",
    "quantity",
    "unit_price",
]

missing_required = df[required_fields].isna().any(axis=1)


for column in ["customer_name", "email", "product"]:
    missing_required |= df[column].eq("").fillna(False)


valid_email = df["email"].str.match(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
    na=False,
)

invalid_email = ~valid_email


invalid_quantity = df["quantity"].isna() | (df["quantity"] <= 0)
invalid_price = df["unit_price"].isna() | (df["unit_price"] < 0)


df["rejection_reason"] = ""

checks = [
    (missing_required, "Missing required field or invalid date/number"),
    (invalid_email, "Invalid email"),
    (invalid_quantity, "Quantity must be greater than zero"),
    (invalid_price, "Price cannot be negative"),
]

for mask, reason in checks:
    df.loc[mask, "rejection_reason"] = (
            df.loc[mask, "rejection_reason"]
            .apply(lambda current: f"{current}; " if current else "")
            + reason
    )


rejected = df[df["rejection_reason"] != ""].copy()
valid = df[df["rejection_reason"] == ""].copy()


valid["order_total"] = valid["quantity"] * valid["unit_price"]


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

valid.to_csv(OUTPUT_DIR / "cleaned_orders.csv", index=False)
rejected.to_csv(OUTPUT_DIR / "rejected_orders.csv", index=False)

print("\n=== DATA QUALITY REPORT ===")
print(f"Original rows: {len(pd.read_csv(DATA_FILE))}")
print(f"Exact duplicate rows removed: {duplicate_count}")
print(f"Rows after deduplication: {len(df)}")
print(f"Valid records: {len(valid)}")
print(f"Rejected records: {len(rejected)}")
print(f"Data acceptance rate: {len(valid) / len(df) * 100:.1f}%")


print("\n=== REJECTION REASONS ===")

if rejected.empty:
    print("No rejected records.")
else:
    print(
        rejected[
            ["order_id", "customer_name", "rejection_reason"]
        ].to_string(index=False)
    )

    
    issue_counts = (
        rejected["rejection_reason"]
        .str.split("; ")
        .explode()
        .value_counts()
    )

    print("\n=== VALIDATION ISSUES BY TYPE ===")
    print(issue_counts.to_string())

