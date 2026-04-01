from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

def fix_sequence():
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+pg8000://postgres:1234@localhost:5432/postgres"
    )
    
    print(f"[FIX_DB] Connecting to {db_url}...")
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get max ID from "user" table
        res = session.execute(text("SELECT MAX(id) FROM \"user\";"))
        max_id = res.fetchone()[0]
        
        if max_id is None:
            print("[FIX_DB] User table is empty, nothing to do.")
            session.close()
            return True
            
        print(f"[FIX_DB] Current Max ID in 'user' table: {max_id}")
        
        # Reset sequence
        sql = text(f"SELECT setval('user_id_seq', {max_id});")
        print(f"[FIX_DB] Executing: {sql}")
        session.execute(sql)
        session.commit()
        print("[FIX_DB] Sequence successfully reset.")
        session.close()
        return True
    except Exception as e:
        print(f"[FIX_DB] ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    fix_sequence()
