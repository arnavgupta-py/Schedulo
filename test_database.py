# test_db_access.py
import os
import sqlite3
import sys

# Get absolute path for our working directory
current_dir = os.path.abspath(os.getcwd())
print(f"Current working directory: {current_dir}")

# Define database path using an absolute path to user home directory
# This ensures we have write permissions
home_dir = os.path.expanduser("~")
db_dir = os.path.join(home_dir, "schedulo_data")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "test_schedulo.db")

print(f"Testing database path: {db_path}")

try:
    # Try to create and connect to a SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a simple table
    cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
    
    # Insert a record
    cursor.execute("INSERT INTO test (name) VALUES (?)", ("Test connection",))
    conn.commit()
    
    # Verify record was inserted
    cursor.execute("SELECT * FROM test")
    results = cursor.fetchall()
    print(f"Database test successful! Records: {results}")
    
    conn.close()
    print("Connection closed successfully")
    sys.exit(0)  # Success
except Exception as e:
    print(f"Error accessing database: {e}")
    sys.exit(1)  # Failure