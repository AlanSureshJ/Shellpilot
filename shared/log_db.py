from dotenv import load_dotenv
load_dotenv()
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os


# ✅ Load environment variables from .env file


# ✅ Use env vars from .env
DB_CONFIG = {
    "dbname": "shellpilot_db",
    "user": "shellpilot_user",
    "password": "alan53892",  # hardcoded to test
    "host": "localhost",
    "port": "5432",
}

def log_command(prompt, category, suggested_command, was_run, output=None):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO logs (timestamp, prompt, category, suggested_command, was_run, output)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            datetime.now(),
            prompt,
            category,
            suggested_command,
            was_run,
            (output[:5000] if output else None)
        ))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"⚠️ Failed to log command to DB: {e}")
