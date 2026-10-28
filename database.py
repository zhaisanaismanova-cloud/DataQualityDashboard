
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
DB_FILE = BASE_DIR / "data_quality.db"


def create_tables(connection):
    connection.execute("""
                       CREATE TABLE IF NOT EXISTS cleaned_orders (
                                                                     order_id INTEGER PRIMARY KEY,
                                                                     customer_name TEXT NOT NULL,
                                                                     email TEXT NOT NULL,
                                                                     order_date TEXT NOT NULL,
                                                                     product TEXT NOT NULL,
                                                                     quantity INTEGER NOT NULL CHECK (quantity > 0),
                           unit_price REAL NOT NULL CHECK (unit_price >= 0),
                           order_total REAL NOT NULL CHECK (order_total >= 0)
                           )
                       """)

    connection.execute("""
                       CREATE TABLE IF NOT EXISTS rejected_orders (
                                                                      rejection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                      order_id TEXT,
                                                                      customer_name TEXT,
                                                                      email TEXT,
                                                                      rejection_reason TEXT NOT NULL
                       )
                       """)


def load_cleaned_orders(connection):
    file_path = OUTPUT_DIR / "cleaned_orders.csv"
    df = pd.read_csv(file_path)

    # Store dates as ISO-formatted strings in SQLite.
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m-%d")

    # Convert validated quantities to integers.
    df["quantity"] = df["quantity"].astype(int)

    df.to_sql(
        "cleaned_orders",
        connection,
        if_exists="replace",
        index=False,
    )

    print(f"Loaded {len(df)} cleaned orders into SQLite.")


def load_rejected_orders(connection):
    file_path = OUTPUT_DIR / "rejected_orders.csv"
    df = pd.read_csv(file_path)

    df = df[[
        "order_id",
        "customer_name",
        "email",
        "rejection_reason",
    ]].copy()

    df.to_sql(
        "rejected_orders",
        connection,
        if_exists="replace",
        index=False,
    )

    print(f"Loaded {len(df)} rejected orders into SQLite.")


def show_sql_summary(connection):
    print("\n=== SQL SUMMARY ===")

    query = """
            SELECT
                COUNT(*) AS total_orders,
                ROUND(SUM(order_total), 2) AS total_sales,
                ROUND(AVG(order_total), 2) AS average_order_value
            FROM cleaned_orders \
            """

    result = pd.read_sql_query(query, connection)
    print(result.to_string(index=False))

    print("\n=== SALES BY PRODUCT ===")

    query = """
            SELECT
                product,
                SUM(quantity) AS units_sold,
                ROUND(SUM(order_total), 2) AS sales
            FROM cleaned_orders
            GROUP BY product
            ORDER BY sales DESC \
            """

    result = pd.read_sql_query(query, connection)
    print(result.to_string(index=False))


def main():
    # First, run clean_data.py so the CSV outputs exist.
    if not (OUTPUT_DIR / "cleaned_orders.csv").exists():
        print("Please run clean_data.py first.")
        return

    with sqlite3.connect(DB_FILE) as connection:
        create_tables(connection)
        load_cleaned_orders(connection)
        load_rejected_orders(connection)

        # Recreate constraints after loading data using pandas.
        connection.execute("DROP TABLE IF EXISTS cleaned_orders_constrained")
        connection.execute("""
                           CREATE TABLE cleaned_orders_constrained (
                                                                       order_id INTEGER PRIMARY KEY,
                                                                       customer_name TEXT NOT NULL,
                                                                       email TEXT NOT NULL,
                                                                       order_date TEXT NOT NULL,
                                                                       product TEXT NOT NULL,
                                                                       quantity INTEGER NOT NULL CHECK (quantity > 0),
                                                                       unit_price REAL NOT NULL CHECK (unit_price >= 0),
                                                                       order_total REAL NOT NULL CHECK (order_total >= 0)
                           )
                           """)

        connection.execute("""
                           INSERT INTO cleaned_orders_constrained
                           SELECT
                               order_id, customer_name, email, order_date,
                               product, quantity, unit_price, order_total
                           FROM cleaned_orders
                           """)

        connection.execute("DROP TABLE cleaned_orders")
        connection.execute("""
                           ALTER TABLE cleaned_orders_constrained
                               RENAME TO cleaned_orders
                           """)

        show_sql_summary(connection)

    print(f"\nDatabase created at: {DB_FILE}")


if __name__ == "__main__":
    main()
