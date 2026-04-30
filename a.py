# fix_db.py
import psycopg2

# Paste your full Internal Database URL from Render here
DATABASE_URL = "postgresql://nutriveda_0e4l_user:AVVinSOgP8mFcfhqBGxJVu6YGq8rwKcz@dpg-d7p9iqf7f7vs73c7ade0-a.singapore-postgres.render.com/nutriveda_0e4l"

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(256);")
    print("✅ Column altered successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")