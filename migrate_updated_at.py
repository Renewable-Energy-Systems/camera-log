import sqlite3
from core.paths import DB_PATH

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    with sqlite3.connect(DB_PATH) as con:
        try:
            # Check if column exists
            cur = con.execute("PRAGMA table_info(recordings)")
            columns = [row[1] for row in cur.fetchall()]
            
            if "updated_at" not in columns:
                print("Adding updated_at column...")
                con.execute("ALTER TABLE recordings ADD COLUMN updated_at TEXT")
                con.commit()
                print("Migration successful.")
            else:
                print("Column updated_at already exists.")
                
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
