#!/usr/bin/env python
import sys
import os
from sqlalchemy import create_engine, text

db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+pg8000://postgres:1234@localhost:5432/postgres",
)

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, username, login_timestamp, logout_timestamp, duration_seconds FROM login_audit LIMIT 5"))
        for row in result:
            print(f"ID: {row[0]}, User: {row[1]}, Login: {row[2]}, Logout: {row[3]}, Duration: {row[4]}")
except Exception as e:
    print(f"Error: {e}")
