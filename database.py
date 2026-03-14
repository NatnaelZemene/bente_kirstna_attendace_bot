import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

def create_tables():
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        username TEXT,
        first_name TEXT
    )
    """)

    # Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions(
        id SERIAL PRIMARY KEY,
        session_name TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP
    )
    """)

    # Attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        session_id INTEGER,
        join_time TIMESTAMP,
        leave_time TIMESTAMP
    )
    """)

    conn.commit()