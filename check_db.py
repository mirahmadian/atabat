import sqlite3

DB_PATH = "atabat.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# بررسی وجود جدول rahnama
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rahnama'")
table_exists = cursor.fetchone()

if table_exists:
    print("✅ جدول 'rahnama' وجود دارد.")
    
    # نمایش ساختار جدول
    cursor.execute("PRAGMA table_info(rahnama)")
    columns = cursor.fetchall()
    print("ساختار جدول rahnama:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
else:
    print("❌ جدول 'rahnama' وجود ندارد.")

conn.close()
