"""Скрипт для ожидания готовности базы данных."""
import sys
import time
from sqlalchemy import create_engine, text
from app.config import config

for i in range(30):
    try:
        engine = create_engine(config.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database is ready!")
        sys.exit(0)
    except Exception as e:
        if i == 0:
            print(f"Waiting for database... (attempt {i+1}/30)")
        elif i % 5 == 0:
            print(f"Still waiting... (attempt {i+1}/30)")
        time.sleep(1)

print("Database connection timeout!")
sys.exit(1)

