import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    # Get DB path from env or default
    db_uri = os.environ.get('DATABASE_URI', 'sqlite:///leadscan.db')
    db_path = db_uri.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    print(f"p Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define new columns to add
    new_columns = [
        ('status_code', 'INTEGER'),
        ('analysis_error', 'VARCHAR(500)'),
        ('analysis_notes', 'TEXT'),
        ('copyright_year', 'INTEGER'),
        ('tech_stack', 'VARCHAR(100)'),
        ('load_time', 'INTEGER')
    ]

    # Get existing columns
    cursor.execute("PRAGMA table_info(leads)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    added_count = 0
    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            print(f"➕ Adding column: {col_name} ({col_type})")
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                added_count += 1
            except Exception as e:
                print(f"⚠️ Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    
    if added_count > 0:
        print(f"✅ Migration complete. Added {added_count} columns.")
    else:
        print("ℹ️ No migration needed (columns already exist).")

if __name__ == "__main__":
    migrate()
