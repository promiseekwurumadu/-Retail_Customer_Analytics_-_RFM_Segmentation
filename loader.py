# loader.py
# Loads our raw CSV files into PostgreSQL
# In a real job this step is replaced by:
# - Direct database access (most common)
# - API connection
# - ETL tool like Talend or Azure Data Factory
# The SQL and cleaning logic below stays identical

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import psycopg2
from config import CONNECTION_STRING, DB_CONFIG
import os

engine = create_engine(CONNECTION_STRING)

# ── STEP 1: CREATE TABLES ─────────────────────────────────────────
def create_tables():
    """
    Creates our database schema — the structure of our tables
    before we put any data in them
    Think of it like drawing the columns of a spreadsheet
    before filling in the rows
    """
    print("\n  Creating database tables...")

    with engine.connect() as conn:

        # Drop tables if they already exist
        # This lets us re-run the loader safely
        conn.execute(text("""
            DROP TABLE IF EXISTS transactions CASCADE;
            DROP TABLE IF EXISTS customers   CASCADE;
            DROP TABLE IF EXISTS products    CASCADE;
            DROP TABLE IF EXISTS stores      CASCADE;
        """))

        # CUSTOMERS table
        conn.execute(text("""
            CREATE TABLE customers (
                customer_id     VARCHAR(10)  PRIMARY KEY,
                full_name       VARCHAR(100),
                email           VARCHAR(100),
                phone           VARCHAR(30),
                region          VARCHAR(50),
                postcode        VARCHAR(10),
                signup_date     DATE,
                loyalty_member  BOOLEAN,
                age_group       VARCHAR(10)
            );
        """))

        # PRODUCTS table
        conn.execute(text("""
            CREATE TABLE products (
                product_id      VARCHAR(8)   PRIMARY KEY,
                product_name    VARCHAR(100),
                category        VARCHAR(50),
                description     VARCHAR(200),
                sell_price      NUMERIC(10,2),
                cost_price      NUMERIC(10,2),
                supplier        VARCHAR(100),
                in_stock        BOOLEAN,
                launch_date     DATE
            );
        """))

        # STORES table
        conn.execute(text("""
            CREATE TABLE stores (
                store_id        VARCHAR(6)   PRIMARY KEY,
                store_name      VARCHAR(100),
                region          VARCHAR(50),
                postcode        VARCHAR(10),
                store_size_sqft INTEGER,
                num_staff       INTEGER,
                manager_name    VARCHAR(100),
                opening_date    DATE,
                is_flagship     BOOLEAN
            );
        """))

        # TRANSACTIONS table
        # This is our biggest table — 50,000 rows
        # foreign keys link back to the other tables
        conn.execute(text("""
            CREATE TABLE transactions (
                transaction_id   VARCHAR(10)  PRIMARY KEY,
                transaction_date DATE,
                customer_id      VARCHAR(10)  REFERENCES customers(customer_id),
                product_id       VARCHAR(8)   REFERENCES products(product_id),
                store_id         VARCHAR(6)   REFERENCES stores(store_id),
                quantity         INTEGER,
                unit_price       NUMERIC(10,2),
                discount_pct     NUMERIC(5,2),
                total_value      NUMERIC(10,2),
                payment_method   VARCHAR(20),
                channel          VARCHAR(10)
            );
        """))

        conn.commit()
        print("  Tables created successfully!")

# ── STEP 2: CLEAN AND LOAD CUSTOMERS ─────────────────────────────
def load_customers():
    print("\n  Loading customers...")
    df = pd.read_csv('raw_data/customers_raw.csv')
    print(f"  Raw rows: {len(df)}")

    # Fix name casing — Title Case for all names
    df['full_name'] = df['full_name'].str.title()

    # Remove duplicate customer IDs — keep first occurrence
    df = df.drop_duplicates(subset=['customer_id'])

    # Standardise email to lowercase
    df['email'] = df['email'].str.lower()

    # Convert signup_date to proper date
    df['signup_date'] = pd.to_datetime(
                            df['signup_date']
                        ).dt.date

    df.to_sql(
        'customers', engine,
        if_exists='append',
        index=False
    )
    print(f"  Customers loaded: {len(df)} rows")
    return df

# ── STEP 3: CLEAN AND LOAD PRODUCTS ──────────────────────────────
def load_products():
    print("\n  Loading products...")
    df = pd.read_csv('raw_data/products_raw.csv')
    print(f"  Raw rows: {len(df)}")

    # Fix category casing — some were UPPER, some lower
    # Title Case standardises everything
    df['category'] = df['category'].str.strip().str.title()

    # Remove £ symbol from prices stored as strings
    df['sell_price'] = df['sell_price'].astype(str)\
                         .str.replace('£', '', regex=False)\
                         .astype(float)

    # Fill missing cost prices with 60% of sell price
    # (industry average margin assumption)
    df['cost_price'] = df.apply(
        lambda r: r['sell_price'] * 0.60
                  if pd.isna(r['cost_price'])
                  else r['cost_price'],
        axis=1
    )

    # Convert launch_date to proper date
    df['launch_date'] = pd.to_datetime(
                            df['launch_date']
                        ).dt.date

    df.to_sql(
        'products', engine,
        if_exists='append',
        index=False
    )
    print(f"  Products loaded: {len(df)} rows")
    return df

# ── STEP 4: CLEAN AND LOAD STORES ────────────────────────────────
def load_stores():
    print("\n  Loading stores...")
    df = pd.read_csv('raw_data/stores_raw.csv')
    print(f"  Raw rows: {len(df)}")

    # Fix inconsistent region names
    # Store data used different names to customer data
    region_map = {
        'Greater London'        : 'London',
        'SE England'            : 'South East',
        'NW England'            : 'North West',
        'Yorkshire & Humber'    : 'Yorkshire',
        'W. Midlands'           : 'West Midlands',
        'East England'          : 'East of England',
        'SW England'            : 'South West',
        'NE England'            : 'North East',
        'Scotland'              : 'Scotland',
        'Wales'                 : 'Wales'
    }
    df['region'] = df['region'].map(region_map)\
                               .fillna(df['region'])

    # Fix mixed date formats (DD/MM/YYYY and YYYY-MM-DD)
    # Fix mixed date formats (DD/MM/YYYY and YYYY-MM-DD)
    # format='mixed' tells pandas to figure out each date individually
    # dayfirst=True tells it DD comes before MM when ambiguous
    df['opening_date'] = pd.to_datetime(
        df['opening_date'],
        format='mixed',
        dayfirst=True
    ).dt.date

    df.to_sql(
        'stores', engine,
        if_exists='append',
        index=False
    )
    print(f"  Stores loaded: {len(df)} rows")
    return df

# ── STEP 5: CLEAN AND LOAD TRANSACTIONS ──────────────────────────
def load_transactions(customers_df, products_df, stores_df):
    print("\n  Loading transactions (largest table)...")
    df = pd.read_csv('raw_data/transactions_raw.csv')
    print(f"  Raw rows: {len(df)}")

    # Get valid IDs from already-loaded tables
    valid_customers = set(customers_df['customer_id'].unique())
    valid_products  = set(products_df['product_id'].unique())
    valid_stores    = set(stores_df['store_id'].unique())

    # Only keep customer_id if it exists in customers table
    df['customer_id'] = df['customer_id'].apply(
        lambda x: x if x in valid_customers else None
    )

    # Remove transactions with invalid product IDs
    df = df[df['product_id'].isin(valid_products)]

    # Only keep store_id if it exists in stores table
    df['store_id'] = df['store_id'].apply(
        lambda x: x if x in valid_stores else None
    )

    # Convert date
    df['transaction_date'] = pd.to_datetime(
                                 df['transaction_date']
                             ).dt.date

    # Remove duplicate transaction IDs
    df = df.drop_duplicates(subset=['transaction_id'])

    # Load in chunks — good practice for large tables
    chunk_size = 5000
    total      = 0
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        chunk.to_sql(
            'transactions', engine,
            if_exists='append',
            index=False
        )
        total += len(chunk)
        print(f"  Loaded {total:,} / {len(df):,} rows...",
              end='\r')

    print(f"\n  Transactions loaded: {total:,} rows")
    return df

# ── STEP 6: VERIFY EVERYTHING LOADED ─────────────────────────────
def verify_load():
    print("\n  Verifying data load...")
    with engine.connect() as conn:
        for table in ['customers','products',
                      'stores','transactions']:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            )
            count = result.fetchone()[0]
            print(f"  {table:15} : {count:>7,} rows")

# ── MASTER FUNCTION ───────────────────────────────────────────────
def run_loader():
    print("\n" + "="*55)
    print("  RETAIL ANALYTICS — DATA LOADER")
    print("  Loading 4 tables into PostgreSQL")
    print("="*55)

    create_tables()
    customers_df    = load_customers()
    products_df     = load_products()
    stores_df       = load_stores()
    transactions_df = load_transactions(
                        customers_df,
                        products_df,
                        stores_df
                      )
    verify_load()

    print("\n" + "="*55)
    print("  LOAD COMPLETE")
    print("  Open pgAdmin to browse your data!")
    print("="*55)

if __name__ == '__main__':
    run_loader()