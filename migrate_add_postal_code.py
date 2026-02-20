"""
Migration: Add postal_code column to clients table.
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "invoices.db")

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(clients)")
columns = [row[1] for row in cursor.fetchall()]

if "postal_code" in columns:
    print("Column 'postal_code' already exists in clients table. Nothing to do.")
else:
    cursor.execute("ALTER TABLE clients ADD COLUMN postal_code VARCHAR(20) DEFAULT ''")
    conn.commit()
    print("✓ Added 'postal_code' column to clients table successfully.")

conn.close()
