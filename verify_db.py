import sqlite3
from pathlib import Path

DB_PATH = Path("res_stack_recorder.db")

def verify():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    print("Verifying database...")
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        
        # Check columns
        print("Columns in 'recordings':")
        cur.execute("PRAGMA table_info(recordings)")
        columns = [row[1] for row in cur.fetchall()]
        print(columns)
        
        if "battery_name" in columns and "battery_code" in columns:
            print("SUCCESS: New columns found.")
        else:
            print("FAILURE: New columns NOT found.")

        if "project_name" not in columns and "project_no" not in columns:
             print("SUCCESS: Old columns removed.")
        else:
             print("FAILURE: Old columns still present.")

        # Check data
        print("\nFirst 3 rows:")
        cur.execute("SELECT * FROM recordings LIMIT 3")
        rows = cur.fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    verify()
