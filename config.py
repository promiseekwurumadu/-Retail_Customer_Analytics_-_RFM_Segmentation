# config.py
# Stores database connection settings in one place
# Think of this like saving your WiFi password —
# you only type it once and everything else uses it

DB_CONFIG = {
    'host'    : 'localhost',       # your computer
    'port'    : 5432,              # default PostgreSQL port
    'database': 'retail_analytics',
    'user'    : 'postgres',        # default PostgreSQL username
    'password': '4010983003pro'    # replace with your actual password
}

# Connection string for SQLAlchemy
# SQLAlchemy is a Python library that talks to PostgreSQL
CONNECTION_STRING = (
    f"postgresql+psycopg2://"
    f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
    f"/{DB_CONFIG['database']}"
)