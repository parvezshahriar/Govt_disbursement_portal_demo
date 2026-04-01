import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Session, Base
from dbmodel import Product, ClientInfo
from sqlalchemy import text

def migrate():
    print("[MIGRATION] Starting beneficiary migration...")
    db = Session()
    try:
        # 1. Create client_info table if it doesnt exist
        Base.metadata.create_all(bind=engine)
        print("[MIGRATION] Table client_info ensured.")

        # 2. Get unique beneficiaries from product_1
        print("[MIGRATION] Fetching unique beneficiaries from product_1...")
        # We group by BENEFICIARY_ID and take the latest info (or just any)
        # Note: In a real scenario, we might want to handle data inconsistencies
        products = db.query(Product).all()
        
        beneficiaries = {}
        for p in products:
            if p.BENEFICIARY_ID not in beneficiaries:
                beneficiaries[p.BENEFICIARY_ID] = {
                    'BENEFICIARY_ID': p.BENEFICIARY_ID,
                    'name': p.CRACCOUNTTITLE,
                    'CRACCOUNTNO': p.CRACCOUNTNO,
                    'CRACCOUNTTYPE': p.CRACCOUNTTYPE,
                    'CRROUTINGNO': p.CRROUTINGNO,
                    'MOBILE': p.MOBILE,
                    'NID_NO': p.NID_NO
                }
        
        print(f"[MIGRATION] Found {len(beneficiaries)} unique beneficiaries.")

        # 3. Insert into client_info
        success_count = 0
        error_count = 0
        for bid, data in beneficiaries.items():
            try:
                # Check if already exists
                existing = db.query(ClientInfo).filter(ClientInfo.BENEFICIARY_ID == bid).first()
                if not existing:
                    client = ClientInfo(
                        BENEFICIARY_ID=data['BENEFICIARY_ID'],
                        name=data['name'],
                        CRACCOUNTNO=data['CRACCOUNTNO'],
                        CRACCOUNTTYPE=data['CRACCOUNTTYPE'],
                        CRROUTINGNO=data['CRROUTINGNO'],
                        MOBILE=data['MOBILE'],
                        NID_NO=data['NID_NO']
                    )
                    db.add(client)
                    success_count += 1
                else:
                    print(f"[MIGRATION] Beneficiary {bid} already exists in client_info.")
            except Exception as e:
                print(f"[MIGRATION] Error migrating beneficiary {bid}: {e}")
                error_count += 1
        
        db.commit()
        print(f"[MIGRATION] Successfully migrated {success_count} beneficiaries. Errors: {error_count}")

        # 4. Optional: Verify foreign key constraint
        # In SQLite/Postgres, the constraint is now in the model, 
        # but existing data in product_1 should already have valid BENEFICIARY_IDs.
        
        print("[MIGRATION] Migration completed successfully!")
        return True
    except Exception as e:
        db.rollback()
        print(f"[MIGRATION] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
