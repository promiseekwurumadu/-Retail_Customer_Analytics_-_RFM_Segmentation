# test_connection.py
# Checks that Python can talk to PostgreSQL
# Like making a test call before an important meeting

import psycopg2
from config import DB_CONFIG

try:
    # Try to connect
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Ask PostgreSQL for its version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

    print("Connection successful!")
    print(f"PostgreSQL version: {version[:50]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Connection failed: {e}")
    print("\nCommon fixes:")
    print("  - Check your password in config.py")
    print("  - Make sure PostgreSQL service is running")
    print("  - Check port 5432 is not blocked")