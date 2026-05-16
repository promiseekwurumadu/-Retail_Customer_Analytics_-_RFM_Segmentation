# generate_data.py
# Generates three realistic messy retail datasets
# simulating data extracted from three different
# business systems that don't talk to each other
#
# Real equivalent data sources:
# - Transactions: UK Retail Sales (ONS) structure
# - Products: GS1 UK product catalogue format
# - Stores: based on real UK retail store formats

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker('en_GB')  # UK locale — British names, postcodes, addresses
np.random.seed(42)
random.seed(42)

os.makedirs('raw_data', exist_ok=True)

# ── REFERENCE DATA ────────────────────────────────────────────────

UK_REGIONS = [
    'London', 'South East', 'North West', 'Yorkshire',
    'West Midlands', 'East of England', 'South West',
    'Scotland', 'Wales', 'North East'
]

PRODUCT_CATEGORIES = {
    'Electronics'   : ['Laptop', 'Phone', 'Tablet', 'Headphones',
                       'Smart Watch', 'Camera', 'Speaker'],
    'Clothing'      : ['T-Shirt', 'Jeans', 'Jacket', 'Dress',
                       'Shoes', 'Trainers', 'Coat'],
    'Food & Drink'  : ['Coffee', 'Tea', 'Biscuits', 'Chocolate',
                       'Wine', 'Beer', 'Juice'],
    'Home & Garden' : ['Lamp', 'Cushion', 'Plant Pot', 'Candle',
                       'Picture Frame', 'Rug', 'Vase'],
    'Sports'        : ['Yoga Mat', 'Dumbbells', 'Running Shoes',
                       'Water Bottle', 'Gym Bag', 'Resistance Bands'],
    'Beauty'        : ['Moisturiser', 'Shampoo', 'Perfume',
                       'Lipstick', 'Face Mask', 'Body Lotion']
}

PRICE_RANGES = {
    'Electronics'   : (49.99,  1299.99),
    'Clothing'      : (9.99,   149.99),
    'Food & Drink'  : (1.99,   29.99),
    'Home & Garden' : (4.99,   89.99),
    'Sports'        : (9.99,   199.99),
    'Beauty'        : (3.99,   79.99)
}

# ── GENERATE CUSTOMERS ────────────────────────────────────────────

def generate_customers(n=2000):
    """
    Generates 2000 UK customers with realistic attributes
    Includes real-world messiness:
    - Mixed case names
    - Some missing email addresses
    - Inconsistent phone formats
    - Some duplicate-ish records
    """
    print("  Generating customers...")
    customers = []

    for i in range(n):
        region  = random.choice(UK_REGIONS)
        signup  = fake.date_between(
                    start_date='-3y',
                    end_date='today'
                  )

        # Realistic messiness — some missing emails (8%)
        email = fake.email() if random.random() > 0.08 else None

        # Phone format inconsistency — real world problem
        phone_format = random.choice(['07xxx xxxxxx', '07xxxxxxxxx', '+447xxxxxxxxx'])
        phone = fake.phone_number()

        # Some customers have inconsistent name casing
        name = fake.name()
        if random.random() < 0.15:
            name = name.upper()  # some system exported in caps
        elif random.random() < 0.10:
            name = name.lower()  # another system used lowercase

        customers.append({
            'customer_id'   : f'CUST{str(i+1).zfill(5)}',
            'full_name'     : name,
            'email'         : email,
            'phone'         : phone,
            'region'        : region,
            'postcode'      : fake.postcode(),
            'signup_date'   : signup,
            'loyalty_member': random.choice([True, False, True]),
            'age_group'     : random.choice(
                                ['18-25','26-35','36-45','46-55','55+']
                              )
        })

    # Add ~3% duplicates (same customer, slight variation)
    n_dupes = int(n * 0.03)
    for _ in range(n_dupes):
        original = random.choice(customers)
        dupe     = original.copy()
        # Slightly different — maybe a typo in name
        dupe['customer_id'] = f"CUST{str(random.randint(90000,99999))}"
        dupe['email']       = dupe['email'].replace('.', '_') \
                              if dupe['email'] else None
        customers.append(dupe)

    df = pd.DataFrame(customers)
    df.to_csv('raw_data/customers_raw.csv', index=False)
    print(f"  Customers: {len(df)} rows saved")
    return df

# ── GENERATE PRODUCTS ─────────────────────────────────────────────

def generate_products(n=500):
    """
    Generates 500 products across 6 categories
    Messiness includes:
    - Some missing cost prices
    - Inconsistent category naming (Electronics vs ELECTRONICS)
    - Some products with no description
    - Prices stored as strings in some rows
    """
    print("  Generating products...")
    products = []
    product_id = 1

    for category, items in PRODUCT_CATEGORIES.items():
        n_per_category = n // len(PRODUCT_CATEGORIES)

        for _ in range(n_per_category):
            item         = random.choice(items)
            brand        = fake.company().split()[0]
            min_p, max_p = PRICE_RANGES[category]
            sell_price   = round(random.uniform(min_p, max_p), 2)
            cost_price   = round(sell_price * random.uniform(0.4, 0.75), 2)

            # Messiness — some missing cost prices (12%)
            if random.random() < 0.12:
                cost_price = None

            # Inconsistent category casing (20% of rows)
            cat_name = category
            if random.random() < 0.10:
                cat_name = category.upper()
            elif random.random() < 0.10:
                cat_name = category.lower()

            # Some prices stored as strings with £ symbol
            if random.random() < 0.08:
                sell_price = f"£{sell_price}"

            # Some missing descriptions (15%)
            description = f"{brand} {item}" \
                          if random.random() > 0.15 else None

            products.append({
                'product_id'    : f'PROD{str(product_id).zfill(4)}',
                'product_name'  : f"{brand} {item}",
                'category'      : cat_name,
                'description'   : description,
                'sell_price'    : sell_price,
                'cost_price'    : cost_price,
                'supplier'      : fake.company(),
                'in_stock'      : random.choice([True, True, True, False]),
                'launch_date'   : fake.date_between(
                                    start_date='-5y',
                                    end_date='today'
                                  )
            })
            product_id += 1

    df = pd.DataFrame(products)
    df.to_csv('raw_data/products_raw.csv', index=False)
    print(f"  Products: {len(df)} rows saved")
    return df

# ── GENERATE STORES ───────────────────────────────────────────────

def generate_stores(n=50):
    """
    Generates 50 UK retail stores
    Messiness includes:
    - Region names inconsistent with customer data
    - Some missing manager names
    - Opening dates in different formats
    """
    print("  Generating stores...")
    stores = []

    # Deliberately inconsistent region names vs customer data
    # Customer data uses 'North West'
    # Store data uses 'NW England' — same region, different name!
    store_regions = {
        'London'            : 'Greater London',
        'South East'        : 'SE England',
        'North West'        : 'NW England',      # mismatch!
        'Yorkshire'         : 'Yorkshire & Humber',
        'West Midlands'     : 'W. Midlands',     # mismatch!
        'East of England'   : 'East England',
        'South West'        : 'SW England',
        'Scotland'          : 'Scotland',
        'Wales'             : 'Wales',
        'North East'        : 'NE England'
    }

    for i in range(n):
        region      = random.choice(UK_REGIONS)
        open_date   = fake.date_between(
                        start_date='-10y',
                        end_date='-1y'
                      )

        # Some dates in different format — DD/MM/YYYY vs YYYY-MM-DD
        if random.random() < 0.3:
            open_date = open_date.strftime('%d/%m/%Y')
        else:
            open_date = str(open_date)

        stores.append({
            'store_id'      : f'STR{str(i+1).zfill(3)}',
            'store_name'    : f"{fake.city()} {random.choice(['Retail Park','High Street','Shopping Centre','Superstore'])}",
            'region'        : store_regions[region],
            'postcode'      : fake.postcode(),
            'store_size_sqft': random.randint(2000, 25000),
            'num_staff'     : random.randint(10, 150),
            'manager_name'  : fake.name() if random.random() > 0.1 else None,
            'opening_date'  : open_date,
            'is_flagship'   : random.random() < 0.15
        })

    df = pd.DataFrame(stores)
    df.to_csv('raw_data/stores_raw.csv', index=False)
    print(f"  Stores: {len(df)} rows saved")
    return df

# ── GENERATE TRANSACTIONS ─────────────────────────────────────────

def generate_transactions(customers_df, products_df,
                           stores_df, n=50000):
    """
    Generates 50,000 retail transactions over 2 years
    This is the main fact table — the heart of retail analytics
    Messiness includes:
    - Some missing store IDs (online orders)
    - Negative quantities (returns)
    - Some transactions with no customer (guest checkout)
    - Weekend and seasonal spikes (realistic pattern)
    """
    print("  Generating transactions (this may take 30 seconds)...")

    customer_ids = customers_df['customer_id'].tolist()
    product_ids  = products_df['product_id'].tolist()
    store_ids    = stores_df['store_id'].tolist()

    # Get price lookup — handle string prices
    price_lookup = {}
    for _, row in products_df.iterrows():
        try:
            price = float(str(row['sell_price']).replace('£',''))
        except:
            price = 9.99
        price_lookup[row['product_id']] = price

    transactions = []
    start_date   = datetime(2022, 1, 1)
    end_date     = datetime(2023, 12, 31)
    date_range   = (end_date - start_date).days

    for i in range(n):
        # Realistic date distribution
        # More transactions at weekends and December
        rand_days = random.randint(0, date_range)
        tx_date   = start_date + timedelta(days=rand_days)

        # December spike — 40% more transactions
        if tx_date.month == 12:
            if random.random() < 0.4:
                tx_date = tx_date.replace(
                    day=random.randint(1, 24)
                )

        product_id  = random.choice(product_ids)
        unit_price  = price_lookup.get(product_id, 9.99)

        # Mostly positive quantities, some returns (5%)
        quantity    = random.randint(1, 5)
        if random.random() < 0.05:
            quantity = -1  # return

        # 15% online orders — no store ID
        store_id    = random.choice(store_ids) \
                      if random.random() > 0.15 else None

        # 8% guest checkouts — no customer ID
        customer_id = random.choice(customer_ids) \
                      if random.random() > 0.08 else None

        # Discount applied to 20% of transactions
        discount    = round(random.uniform(0.05, 0.30), 2) \
                      if random.random() < 0.20 else 0.0

        total_value = round(
                        unit_price * quantity * (1 - discount), 2
                      )

        transactions.append({
            'transaction_id': f'TXN{str(i+1).zfill(7)}',
            'transaction_date': tx_date.strftime('%Y-%m-%d'),
            'customer_id'   : customer_id,
            'product_id'    : product_id,
            'store_id'      : store_id,
            'quantity'      : quantity,
            'unit_price'    : unit_price,
            'discount_pct'  : discount,
            'total_value'   : total_value,
            'payment_method': random.choice(
                                ['Card','Cash','Card','Card',
                                 'Online','Voucher']
                              ),
            'channel'       : 'Online' if store_id is None \
                               else 'In-Store'
        })

    df = pd.DataFrame(transactions)
    df.to_csv('raw_data/transactions_raw.csv', index=False)
    print(f"  Transactions: {len(df)} rows saved")
    return df

# ── MASTER FUNCTION ───────────────────────────────────────────────

def generate_all():
    print("\n" + "="*55)
    print("  GENERATING RETAIL DATA")
    print("  Simulating 3 separate business systems")
    print("="*55)

    customers_df    = generate_customers(2000)
    products_df     = generate_products(500)
    stores_df       = generate_stores(50)
    transactions_df = generate_transactions(
                        customers_df,
                        products_df,
                        stores_df,
                        50000
                      )

    print("\n" + "="*55)
    print("  DATA GENERATION COMPLETE")
    print(f"  Customers   : 2,000 rows")
    print(f"  Products    : 500 rows")
    print(f"  Stores      : 50 rows")
    print(f"  Transactions: 50,000 rows")
    print(f"  Total       : 52,550 rows across 4 files")
    print(f"  Location    : raw_data/ folder")
    print("="*55)

if __name__ == '__main__':
    generate_all()