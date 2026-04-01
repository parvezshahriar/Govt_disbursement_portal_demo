import sys
import os
from sqlalchemy import text
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.getcwd())

from backend.database import Session, engine

def test_audit_capture():
    print("Starting Audit Capture Verification...")
    db = Session()
    try:
        # 1. Get a user
        user = db.execute(text('SELECT id, username FROM "user" LIMIT 1')).fetchone()
        if not user:
            print("No users found.")
            return
        
        user_id = user.id
        print(f"Using User: {user.username} (ID: {user_id})")
        
        # 2. Update the user itself to trigger an audit log
        print(f"Updating User: {user_id}")
        
        # 3. Set audit session variables and perform update
        print("Setting audit session variables...")
        db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        db.execute(text(f"SET app.current_employee_id = 'EMP-VERIFY'"))
        
        # Toggle is_active
        db.execute(text('UPDATE "user" SET "is_active" = 1 WHERE "id" = :id'), {"id": user_id})
        db.commit()
        print(f"User updated.")
        
        # 4. Verify audit_log entry via raw SQL
        print("Verifying audit_log entry...")
        log = db.execute(text('SELECT * FROM audit_log WHERE table_name = \'user\' AND record_id = :id AND operation = \'UPDATE\' ORDER BY timestamp DESC LIMIT 1'),
                         {"id": str(user_id)}).fetchone()
        
        if log:
            log_dict = dict(log)
            print(f"✓ Found audit log!")
            print(f"  Captured user_id: {log_dict.get('user_id')}")
            print(f"  Captured employee_id: {log_dict.get('employee_id')}")
            
            if int(log_dict.get('user_id')) == user_id:
                print("✓ USER_ID MATCHES SUCCESS!")
            else:
                print("✗ USER_ID MISMATCH!")
        else:
            print("✗ ERROR: Audit log entry not found.")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_audit_capture()
