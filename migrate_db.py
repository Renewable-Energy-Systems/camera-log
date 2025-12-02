import sqlite3
from pathlib import Path

from core import paths

def migrate():
    db_path = paths.get_db_path()
    if not db_path.exists():
        print("Database not found.")
        return

    print("Starting migration...")
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        
        # 1. Rename existing table
        print("Renaming 'recordings' to 'recordings_old'...")
        try:
            cur.execute("ALTER TABLE recordings RENAME TO recordings_old")
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                print("Table 'recordings' not found. Skipping rename.")
            else:
                raise e

        # 2. Create new table with new schema
        print("Creating new 'recordings' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battery_name TEXT,
                battery_code TEXT,
                log_id TEXT,
                battery_no TEXT,
                operator_name TEXT,
                datetime TEXT,
                remarks TEXT,
                video_path TEXT,
                duration_ms INTEGER DEFAULT NULL,
                created_at TEXT
            )
        """)

        # 3. Copy data
        print("Copying data...")
        # Check if recordings_old exists to copy from
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recordings_old'")
        if cur.fetchone():
            cur.execute("""
                INSERT INTO recordings (
                    id, battery_name, battery_code, log_id, battery_no, 
                    operator_name, datetime, remarks, video_path, duration_ms, created_at
                )
                SELECT 
                    id, project_name, project_no, log_id, battery_no, 
                    operator_name, datetime, remarks, video_path, duration_ms, created_at
                FROM recordings_old
            """)
            print(f"Copied {cur.rowcount} rows.")
            
            # 4. Drop old table
            print("Dropping 'recordings_old'...")
            cur.execute("DROP TABLE recordings_old")
        else:
            print("No old data to copy.")

        con.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
