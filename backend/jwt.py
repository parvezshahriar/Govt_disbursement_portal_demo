from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import csv
from datetime import datetime, timedelta
import sys
import os
import shutil
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(__file__))

from dbmodel import Product, User, UserInfo, Image, BatchUpload, ClientInfo
from database import Session
from model import ProductSchema, UserCreate, UserLogin, BatchUploadRequest, UserInfoCreate, UserInfoResponse, ImageResponse, BatchUploadResponse, UserUpdate
from rbac import Permission, has_permission, Role
from login_audit_manager import LoginAuditManager
from audit_log_manager import AuditLogManager
from fastapi import Request

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper function to check user permissions
def check_permission(user_id: int, permission: Permission) -> User:
    """Check if user has the required permission"""
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_role = Role(user.role)
        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. You need '{permission.value}' access"
            )
        
        return user
    finally:
        db.close()


# Registration endpoint
@app.post('/registration')
async def register_user(user: UserCreate):
    db = Session()
    try:
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        db_user = User(
            username=user.username,
            password=user.password,
            email=user.email,
            role=user.role or 'user',
            is_active=1
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return {
            "message": "User registered successfully",
            "id": db_user.id,
            "username": user.username,
            "email": db_user.email,
            "role": db_user.role
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Login endpoint
@app.post('/login')
async def login_user(user: UserLogin, request: Request):
    db = Session()
    try:
        # Extract client IP and user agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent', '')
        
        print(f"[LOGIN] Attempting login for username: {user.username}")
        
        db_user = db.query(User).filter(User.username == user.username).first()

        if not db_user or db_user.password != user.password:
            print(f"[LOGIN] Failed login attempt for {user.username}: Invalid credentials")
            # Log failed login attempt
            try:
                LoginAuditManager.log_login_attempt(
                    username=user.username,
                    email=getattr(db_user, 'email', None) if db_user else None,
                    login_status='FAILED',
                    failure_reason='Invalid credentials',
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                print(f"[LOGIN] Audit log recorded for failed attempt")
            except Exception as audit_err:
                print(f"[LOGIN] Error logging failed attempt: {str(audit_err)}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Check if user is active
        if not db_user.is_active:
            print(f"[LOGIN] Failed login attempt for {user.username}: Account deactivated")
            # Log failed login attempt (account deactivated)
            try:
                LoginAuditManager.log_login_attempt(
                    username=user.username,
                    user_id=db_user.id,
                    email=db_user.email,
                    login_status='FAILED',
                    failure_reason='Account deactivated',
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                print(f"[LOGIN] Audit log recorded for deactivated account")
            except Exception as audit_err:
                print(f"[LOGIN] Error logging deactivated attempt: {str(audit_err)}")
            raise HTTPException(status_code=403, detail="Your account has been deactivated. Please contact administrator.")

        # Log successful login
        print(f"[LOGIN] Successful login for {user.username}")
        login_record = None
        try:
            login_record = LoginAuditManager.log_login_attempt(
                username=db_user.username,
                user_id=db_user.id,
                email=db_user.email,
                login_status='SUCCESS',
                ip_address=client_ip,
                user_agent=user_agent
            )
            print(f"[LOGIN] Audit log recorded successfully, session_id: {login_record.get('session_id')}")
        except Exception as audit_err:
            print(f"[LOGIN] Error logging successful attempt: {str(audit_err)}")
            import traceback
            traceback.print_exc()
        
        return {
            "message": "Login successful",
            "user_id": db_user.id,
            "username": db_user.username,
            "role": db_user.role,
            "session_id": login_record.get('session_id') if login_record else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LOGIN] System error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Log unexpected errors
        try:
            LoginAuditManager.log_login_attempt(
                username=user.username,
                login_status='FAILED',
                failure_reason=f'System error: {str(e)}',
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent', '')
            )
        except Exception as audit_err:
            print(f"[LOGIN] Error logging system error: {str(audit_err)}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Get all users endpoint
@app.get('/users')
async def get_users():
    db = Session()
    try:
        users = db.query(User).all()
        user_list = []
        
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": getattr(user, 'email', ''),
                "role": user.role,
                "status": "Active" if user.is_active else "Inactive",
                "created": datetime.now().strftime('%Y-%m-%d')
            })
        
        return user_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Deactivation/Status Update (Toggle)
@app.put('/users/{user_id}/status')
async def update_user_status(user_id: int, status: dict):
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get employee_id from user_info if available
        user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
        emp_id = user_info.employee_id if user_info and user_info.employee_id else str(user_id)
        
        # Set audit session variables BEFORE updating
        try:
            db.execute(text(f"SET app.current_employee_id = '{emp_id}'"))
            db.execute(text(f"SET app.current_user_id = '{user_id}'"))
        except:
            pass
        
        # Update is_active status (1 for active, 0 for inactive)
        user.is_active = 1 if status.get('is_active', True) else 0
        db.commit()
        db.refresh(user)
        
        return {
            "message": "User status updated successfully",
            "id": user.id,
            "username": user.username,
            "status": "Active" if user.is_active else "Inactive"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Update user endpoint
@app.put('/users/{user_id}')
async def update_user(user_id: int, user_data: UserUpdate, current_user_id: int = Body(..., embed=True)):
    """Update user details - EDIT_USER permission required"""
    # Check permissions
    check_permission(current_user_id, Permission.EDIT_USER)
    
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields if provided
        if user_data.username:
            # Check if username already exists for another user
            existing = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
            user.username = user_data.username
        
        if user_data.password:
            user.password = user_data.password
            
        if user_data.email:
            user.email = user_data.email
            
        if user_data.role:
            user.role = user_data.role
            
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
            
        db.commit()
        db.refresh(user)
        
        return {
            "message": "User updated successfully",
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "status": "Active" if user.is_active else "Inactive"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Delete user endpoint
@app.delete('/users/{user_id}')
async def delete_user(user_id: int, current_user_id: int = Body(..., embed=True)):
    """Delete a user - DELETE_USER permission required"""
    # Check permissions
    check_permission(current_user_id, Permission.DELETE_USER)
    
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent self-deletion
        if user_id == current_user_id:
            raise HTTPException(status_code=400, detail="You cannot delete your own account")
            
        # Optional: Audit logging setup
        try:
            db.execute(text(f"SET app.current_employee_id = '{current_user_id}'"))
        except:
            pass
            
        # Delete related user_info first if exists
        user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
        if user_info:
            db.delete(user_info)
            
        # Delete the user
        db.delete(user)
        db.commit()
        
        return {"status": "success", "message": f"User {user_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# Get all products
@app.get('/product')
def get_products(user_id: int = None):
    """Get all products - VIEW_PRODUCTS permission required"""
    db = Session()
    try:
        # Check permission if user_id provided
        if user_id:
            check_permission(user_id, Permission.VIEW_PRODUCTS)
        
        # Join Product with ClientInfo
        results = db.query(Product, ClientInfo).join(ClientInfo, Product.BENEFICIARY_ID == ClientInfo.BENEFICIARY_ID).all()
        product_list = []
        
        for product, client in results:
            product_data = {
                "EFTREFNUMBER": product.EFTREFNUMBER,
                "CRACCOUNTTITLE": client.name,
                "CRACCOUNTTYPE": client.CRACCOUNTTYPE,
                "CRACCOUNTNO": client.CRACCOUNTNO,
                "CRROUTINGNO": client.CRROUTINGNO,
                "CRAMOUNT": product.CRAMOUNT,
                "BENEFICIARY_ID": client.BENEFICIARY_ID,
                "MOBILE": client.MOBILE,
                "NID_NO": client.NID_NO,
                "MIN_CODE": product.MIN_CODE,
                "DEPT_CODE": product.DEPT_CODE,
                "PAYMENT_CYCLE_NAME_EN": product.PAYMENT_CYCLE_NAME_EN,
                "SCHEME_CODE": product.SCHEME_CODE,
                "gender": getattr(client, 'gender', None)
            }
            product_list.append(product_data)
        
        return product_list
    finally:
        db.close()


# Update product
@app.put('/product/{product_id}')
def update_product(product_id: str, product: ProductSchema, user_id: int = None):
    """Update product - EDIT_PRODUCT permission required"""
    # Check permission if user_id provided
    if user_id:
        check_permission(user_id, Permission.EDIT_PRODUCT)
    
    db = Session()
    try:
        db_product = db.query(Product).filter(Product.EFTREFNUMBER == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get employee_id from user_info if user_id provided
        emp_id = str(user_id) if user_id else None
        if user_id:
            user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
            if user_info and user_info.employee_id:
                emp_id = user_info.employee_id
        
        # Set audit session variables BEFORE updating
        if emp_id:
            try:
                db.execute(text(f"SET app.current_employee_id = '{emp_id}'"))
                db.execute(text(f"SET app.current_user_id = '{user_id}'"))
            except:
                pass

        db_product.CRACCOUNTTITLE = product.CRACCOUNTTITLE
        db_product.CRACCOUNTTYPE = product.CRACCOUNTTYPE
        db_product.CRACCOUNTNO = product.CRACCOUNTNO
        db_product.CRROUTINGNO = product.CRROUTINGNO
        db_product.CRAMOUNT = product.CRAMOUNT
        db_product.MIN_CODE = product.MIN_CODE
        db_product.DEPT_CODE = product.DEPT_CODE
        db_product.PAYMENT_CYCLE_NAME_EN = product.PAYMENT_CYCLE_NAME_EN
        db_product.SCHEME_CODE = product.SCHEME_CODE

        # Update Client Info as well
        client = db.query(ClientInfo).filter(ClientInfo.BENEFICIARY_ID == db_product.BENEFICIARY_ID).first()
        if client:
            client.name = product.CRACCOUNTTITLE
            client.CRACCOUNTTYPE = product.CRACCOUNTTYPE
            client.CRACCOUNTNO = product.CRACCOUNTNO
            client.CRROUTINGNO = product.CRROUTINGNO
            client.MOBILE = product.MOBILE
            client.NID_NO = product.NID_NO

        db.commit()
        db.refresh(db_product)

        return {
            "EFTREFNUMBER": db_product.EFTREFNUMBER,
            "message": "Product and Client information updated successfully"
        }
    finally:
        db.close()


# Delete product
@app.delete('/product/{product_id}')
def delete_product(product_id: str, user_id: int = None):
    """Delete product - DELETE_PRODUCT permission required (Admin only)"""
    # Check permission if user_id provided
    if user_id:
        check_permission(user_id, Permission.DELETE_PRODUCT)
    
    db = Session()
    try:
        db_product = db.query(Product).filter(Product.EFTREFNUMBER == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get employee_id from user_info if user_id provided
        emp_id = str(user_id) if user_id else None
        if user_id:
            user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
            if user_info and user_info.employee_id:
                emp_id = user_info.employee_id
        
        # Set audit session variables BEFORE deleting
        if emp_id:
            try:
                db.execute(text(f"SET app.current_employee_id = '{emp_id}'"))
                db.execute(text(f"SET app.current_user_id = '{user_id}'"))
            except:
                pass

        db.delete(db_product)
        db.commit()

        return {"message": "Product deleted successfully"}
    finally:
        db.close()


# CSV Upload endpoint
@app.post('/csv-upload')
async def upload_csv(file: UploadFile = File(...), user_id: int = None):
    """Upload CSV file - UPLOAD_CSV permission required"""
    # Check permission if user_id provided
    if user_id:
        check_permission(user_id, Permission.UPLOAD_CSV)
    
    db = Session()
    try:
        contents = await file.read()
        csv_text = contents.decode('utf-8')

        reader = csv.DictReader(csv_text.strip().split('\n'))
        success_count = 0
        error_count = 0
        
        # Columns to check for duplicates
        duplicate_check_columns = ['EFTREFNUMBER', 'CRACCOUNTNO', 'BENEFICIARY_ID', 'NID_NO']
        
        # Track values in current CSV and database
        seen_in_csv = {col: set() for col in duplicate_check_columns}
        duplicate_errors = []
        
        # First, check for duplicates in the CSV file itself
        rows_list = list(reader)
        for row_index, row in enumerate(rows_list, start=1):
            for col in duplicate_check_columns:
                value = row.get(col)
                if value and value.strip():  # Only check non-empty values
                    if value in seen_in_csv[col]:
                        duplicate_errors.append(f"Row {row_index}: Duplicate '{col}' found - '{value}'")
                    else:
                        seen_in_csv[col].add(value)

        # If duplicates found in CSV, return error immediately
        if duplicate_errors:
            return {
                "success_count": 0,
                "error_count": len(duplicate_errors),
                "message": "Duplicate data found in CSV file",
                "duplicate_errors": duplicate_errors
            }

        # Now check for duplicates against the database
        db_duplicate_errors = []
        for col in duplicate_check_columns:
            if seen_in_csv[col]:
                # Query database for existing values
                model = Product if col == 'EFTREFNUMBER' else ClientInfo
                query = db.query(model).filter(
                    getattr(model, col).in_(list(seen_in_csv[col]))
                ).all()
                
                if query:
                    for item in query:
                        db_value = getattr(item, col)
                        db_duplicate_errors.append(f"Column '{col}' with value '{db_value}' already exists in database")

        # If duplicates found in database, return error
        if db_duplicate_errors:
            return {
                "success_count": 0,
                "error_count": len(db_duplicate_errors),
                "message": "Data already exists in database",
                "duplicate_errors": db_duplicate_errors
            }

        # Set audit session variables BEFORE creating batch
        if user_id:
            try:
                db.execute(text(f"SET app.current_user_id = '{user_id}'"))
                # Try to get employee_id for user_id
                user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
                if user_info and user_info.employee_id:
                    db.execute(text(f"SET app.current_employee_id = '{user_info.employee_id}'"))
            except:
                pass

        # Create batch upload record
        batch_id = None
        batch_name = f"CSV_Upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db_batch = BatchUpload(
            user_id=user_id,
            batch_name=batch_name,
            upload_date=datetime.now(),
            status='Pending'
        )
        db.add(db_batch)
        db.flush()  # Flush to get the batch ID without committing
        batch_id = db_batch.id
        
        total_amount = 0.0
        error_details = []
        for row_index, row in enumerate(rows_list, start=2):  # Start at 2 (row 1 is header)
            try:
                amount = float(row.get('CRAMOUNT', 0))
                total_amount += amount
                
                # Upsert Client Info
                bid = row.get('BENEFICIARY_ID')
                client = db.query(ClientInfo).filter(ClientInfo.BENEFICIARY_ID == bid).first()
                if not client:
                    client = ClientInfo(BENEFICIARY_ID=bid)
                    db.add(client)
                
                client.name = row.get('CRACCOUNTTITLE')
                client.CRACCOUNTNO = row.get('CRACCOUNTNO')
                client.CRACCOUNTTYPE = row.get('CRACCOUNTTYPE')
                client.CRROUTINGNO = row.get('CRROUTINGNO')
                client.MOBILE = row.get('MOBILE')
                client.NID_NO = row.get('NID_NO')

                product = Product(
                    EFTREFNUMBER=row.get('EFTREFNUMBER'),
                    CRAMOUNT=amount,
                    BENEFICIARY_ID=bid,
                    MIN_CODE=row.get('MIN_CODE'),
                    DEPT_CODE=row.get('DEPT_CODE'),
                    PAYMENT_CYCLE_NAME_EN=row.get('PAYMENT_CYCLE_NAME_EN'),
                    SCHEME_CODE=row.get('SCHEME_CODE'),
                    batch_id=batch_id
                )
                db.add(product)
                db.commit()
                success_count += 1
            except Exception as e:
                db.rollback()
                error_count += 1
                error_msg = str(e)
                # Extract key info from error
                if 'duplicate' in error_msg.lower():
                    error_details.append(f"Row {row_index}: Duplicate value - {error_msg[:100]}")
                elif 'unique' in error_msg.lower():
                    error_details.append(f"Row {row_index}: Already exists - {error_msg[:100]}")
                else:
                    error_details.append(f"Row {row_index}: {error_msg[:100]}")
                print(f"[CSV_UPLOAD] Row {row_index} error: {error_msg}")
        
        # Update batch with final totals
        db_batch.total_rows = success_count
        db_batch.total_amount = total_amount
        db_batch.status = 'Completed' if error_count == 0 else 'Completed with Errors'
        db.commit()

        return {
            "success_count": success_count,
            "error_count": error_count,
            "batch_id": batch_id,
            "batch_name": batch_name,
            "message": f"Processed {success_count} products successfully, {error_count} errors",
            "error_details": error_details if error_count > 0 else []
        }
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if 'db' in locals():
            db.close()


# Batch upload endpoint (JSON from frontend)
@app.post('/upload-batch')
async def upload_batch(request_body: dict = Body(...), user_id: int = None):
    """Batch upload products - PROCESS_VALID_ROWS permission required"""
    # Check permission if user_id provided
    if user_id:
        check_permission(user_id, Permission.PROCESS_VALID_ROWS)
    
    try:
        # Handle both JSON body and query parameter
        from fastapi import Request as FastAPIRequest
        
        # Extract rows from request
        rows = request_body.get('rows', [])
        if not rows:
            return {"success_count": 0, "error_count": 0, "message": "No rows to process"}
        
        print(f"[BATCH] Received {len(rows)} rows to process")
        
        db = Session()
        success_count = 0
        error_count = 0
        
        # Columns to check for duplicates
        duplicate_check_columns = ['EFTREFNUMBER', 'CRACCOUNTNO', 'BENEFICIARY_ID', 'NID_NO']
        
        # Track values in current batch and database
        seen_in_batch = {col: set() for col in duplicate_check_columns}
        duplicate_errors = []
        
        # First, check for duplicates within the batch itself
        for row_index, row in enumerate(rows, start=1):
            # Handle both dict and object types
            row_dict = row if isinstance(row, dict) else row.__dict__
            
            for col in duplicate_check_columns:
                value = row_dict.get(col, None)
                if value and str(value).strip():  # Only check non-empty values
                    if value in seen_in_batch[col]:
                        duplicate_errors.append(f"Row {row_index}: Duplicate '{col}' found - '{value}'")
                    else:
                        seen_in_batch[col].add(value)

        # If duplicates found in batch, return error immediately
        if duplicate_errors:
            db.close()
            return {
                "success_count": 0,
                "error_count": len(duplicate_errors),
                "message": "Duplicate data found in CSV file",
                "error_details": duplicate_errors[:10]
            }

        # Now check for duplicates against the database
        db_duplicate_errors = []
        for col in duplicate_check_columns:
            if seen_in_batch[col]:
                # Query database for existing values
                model = Product if col == 'EFTREFNUMBER' else ClientInfo
                query = db.query(model).filter(
                    getattr(model, col).in_(list(seen_in_batch[col]))
                ).all()
                
                if query:
                    for item in query:
                        db_value = getattr(item, col)
                        db_duplicate_errors.append(f"Column '{col}' with value '{db_value}' already exists in database")

        # If duplicates found in database, return error
        if db_duplicate_errors:
            db.close()
            return {
                "success_count": 0,
                "error_count": len(db_duplicate_errors),
                "message": "Data already exists in database",
                "error_details": db_duplicate_errors[:10]
            }

        # Create batch upload record
        batch_name = f"Batch_Upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        db_batch = BatchUpload(
            user_id=user_id,
            batch_name=batch_name,
            upload_date=datetime.now(),
            status='Pending'
        )
        db.add(db_batch)
        db.flush()  # Flush to get the batch ID
        batch_id = db_batch.id

        try:
            total_amount = 0.0
            error_details = []
            for row_index, row in enumerate(rows, start=1):
                try:
                    # Handle both dict and object types
                    row_dict = row if isinstance(row, dict) else row.__dict__
                    
                    print(f"[BATCH] Processing row {row_index}: {row_dict}")
                    
                    amount = float(row_dict.get('CRAMOUNT') or 0)
                    total_amount += amount
                    
                    # Upsert Client Info
                    bid = row_dict.get('BENEFICIARY_ID')
                    client = db.query(ClientInfo).filter(ClientInfo.BENEFICIARY_ID == bid).first()
                    if not client:
                        client = ClientInfo(BENEFICIARY_ID=bid)
                        db.add(client)
                    
                    client.name = row_dict.get('CRACCOUNTTITLE')
                    client.CRACCOUNTNO = row_dict.get('CRACCOUNTNO')
                    client.CRACCOUNTTYPE = row_dict.get('CRACCOUNTTYPE')
                    client.CRROUTINGNO = row_dict.get('CRROUTINGNO')
                    client.MOBILE = row_dict.get('MOBILE')
                    client.NID_NO = row_dict.get('NID_NO')

                    product = Product(
                        EFTREFNUMBER=row_dict.get('EFTREFNUMBER'),
                        CRAMOUNT=amount,
                        BENEFICIARY_ID=bid,
                        MIN_CODE=row_dict.get('MIN_CODE'),
                        DEPT_CODE=row_dict.get('DEPT_CODE'),
                        PAYMENT_CYCLE_NAME_EN=row_dict.get('PAYMENT_CYCLE_NAME_EN'),
                        SCHEME_CODE=row_dict.get('SCHEME_CODE'),
                        batch_id=batch_id
                    )
                    db.add(product)
                    db.commit()
                    print(f"[BATCH] Successfully added product: {row_dict.get('EFTREFNUMBER')}")
                    success_count += 1
                except Exception as e:
                    db.rollback()
                    error_count += 1
                    error_msg = str(e)
                    if 'duplicate' in error_msg.lower():
                        error_details.append(f"Row {row_index}: Duplicate value - {error_msg[:100]}")
                    elif 'unique' in error_msg.lower():
                        error_details.append(f"Row {row_index}: Already exists - {error_msg[:100]}")
                    else:
                        error_details.append(f"Row {row_index}: {error_msg[:100]}")
                    print(f"[BATCH] Error importing row {row_index}: {error_msg}")
            
            # Update batch with final totals
            db_batch.total_rows = success_count
            db_batch.total_amount = total_amount
            db_batch.status = 'Completed' if error_count == 0 else 'Completed with Errors'
            db.commit()
        finally:
            db.close()

        print(f"[BATCH] Completed - Success: {success_count}, Errors: {error_count}")
        return {
            "success_count": success_count,
            "error_count": error_count,
            "batch_id": batch_id,
            "batch_name": batch_name,
            "message": f"Processed {success_count} products successfully, {error_count} errors",
            "error_details": error_details if error_count > 0 else []
        }
    except Exception as e:
        print(f"[BATCH] Exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== USER PROFILE ENDPOINTS ====================

@app.get("/user-info/{user_id}")
def get_user_info(user_id: int):
    """Get user profile information"""
    try:
        print(f"[USER_INFO] Step 1: Getting profile for user_id: {user_id}")
        
        db = Session()
        try:
            # Step 2: Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"[USER_INFO] Step 2: User not found: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            print(f"[USER_INFO] Step 3: User found: {user.username}")
            
            # Step 4: Get or create user info
            user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
            
            if not user_info:
                print(f"[USER_INFO] Step 4: No profile found, creating empty profile")
                user_info = UserInfo(user_id=user_id)
                db.add(user_info)
                db.commit()
                db.refresh(user_info)
            
            print(f"[USER_INFO] Step 5: Successfully retrieved user profile")
            return {
                "id": user_info.id,
                "user_id": user_info.user_id,
                "first_name": user_info.first_name,
                "last_name": user_info.last_name,
                "phone": user_info.phone,
                "date_of_birth": user_info.date_of_birth,
                "gender": user_info.gender,
                "employee_id": user_info.employee_id,
                "department": user_info.department,
                "position": user_info.position,
                "office_address": user_info.office_address,
                "avatar_url": user_info.avatar_url,
                "created_at": user_info.created_at,
                "updated_at": user_info.updated_at
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        print(f"[USER_INFO] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/user-info/{user_id}")
def update_user_info(user_id: int, user_info_data: UserInfoCreate):
    """Update user profile information"""
    try:
        print(f"[UPDATE_PROFILE] Step 1: Updating profile for user_id: {user_id}")
        
        db = Session()
        try:
            # Step 2: Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"[UPDATE_PROFILE] Step 2: User not found: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            print(f"[UPDATE_PROFILE] Step 3: User found: {user.username}")
            
            # Step 4: Get or create user info
            user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
            
            if not user_info:
                print(f"[UPDATE_PROFILE] Step 4: Creating new profile for user")
                user_info = UserInfo(user_id=user_id)
            else:
                print(f"[UPDATE_PROFILE] Step 4: Existing profile found, updating")
            
            # Step 5: Update fields
            update_data = user_info_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user_info, field, value)
            
            # Get the employee_id for audit logging
            # Priority: from request data > existing record > user_id as fallback
            emp_id = update_data.get('employee_id') or user_info.employee_id or str(user_id)
            
            print(f"[UPDATE_PROFILE] Step 5: Setting audit employee_id to: {emp_id}")
            
            # Set the employee_id for audit logging BEFORE commit
            try:
                db.execute(text(f"SET app.current_employee_id = '{emp_id}'"))
            except Exception as e:
                print(f"[UPDATE_PROFILE] Warning: Could not set session variable: {str(e)}")
            
            print(f"[UPDATE_PROFILE] Step 6: Saving profile changes")
            db.add(user_info)
            db.commit()
            db.refresh(user_info)
            
            print(f"[UPDATE_PROFILE] Step 7: Profile updated successfully with employee_id: {emp_id}")
            return {
                "id": user_info.id,
                "user_id": user_info.user_id,
                "first_name": user_info.first_name,
                "last_name": user_info.last_name,
                "phone": user_info.phone,
                "date_of_birth": user_info.date_of_birth,
                "gender": user_info.gender,
                "employee_id": user_info.employee_id,
                "department": user_info.department,
                "position": user_info.position,
                "office_address": user_info.office_address,
                "avatar_url": user_info.avatar_url,
                "created_at": user_info.created_at,
                "updated_at": user_info.updated_at
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPDATE_PROFILE] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Image upload and retrieval endpoints
UPLOAD_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


@app.post("/image-upload")
async def upload_image(
    file: UploadFile = File(...),
    user_id: int = Form(None),
    product_id: str = Form(None),
    description: str = Form(None)
):
    """Upload an image and store it in the database"""
    try:
        print(f"[IMAGE_UPLOAD] Received upload request")
        print(f"[IMAGE_UPLOAD] File: {file.filename}, Type: {file.content_type}")
        print(f"[IMAGE_UPLOAD] User ID: {user_id}, Product ID: {product_id}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        db = Session()
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + file.filename
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)
            
            print(f"[IMAGE_UPLOAD] Saving file to: {file_path}")
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_size = os.path.getsize(file_path)
            print(f"[IMAGE_UPLOAD] File saved, size: {file_size} bytes")
            
            # Save image record to database
            db_image = Image(
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type,
                user_id=user_id,
                product_id=product_id,
                description=description
            )
            print(f"[IMAGE_UPLOAD] Creating DB record with user_id={user_id}")
            
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            
            print(f"[IMAGE_UPLOAD] Image saved to database with ID: {db_image.id}")
            
            # If this is a profile picture upload, update the user's avatar_url
            if user_id:
                print(f"[IMAGE_UPLOAD] Updating avatar_url for user_id: {user_id}")
                user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
                if user_info:
                    avatar_url = f"/image-view/{db_image.id}"
                    user_info.avatar_url = avatar_url
                    db.commit()
                    print(f"[IMAGE_UPLOAD] Avatar URL updated to: {avatar_url}")
            
            return {
                "message": "Image uploaded successfully",
                "image_id": db_image.id,
                "filename": db_image.filename,
                "original_filename": db_image.original_filename,
                "file_size": file_size,
                "download_url": f"/image/{db_image.id}",
                "view_url": f"/image-view/{db_image.id}"
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


@app.get("/image/{image_id}")
async def download_image(image_id: int):
    """Download/stream an image file"""
    db = Session()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        if not os.path.exists(image.file_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        return FileResponse(
            path=image.file_path,
            filename=image.original_filename,
            media_type=image.mime_type
        )
    finally:
        db.close()


@app.get("/image-view/{image_id}")
async def view_image(image_id: int):
    """View an image (display in browser)"""
    db = Session()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        if not os.path.exists(image.file_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        return FileResponse(
            path=image.file_path,
            media_type=image.mime_type
        )
    finally:
        db.close()


@app.get("/image-info/{image_id}")
async def get_image_info(image_id: int):
    """Get image metadata"""
    db = Session()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "id": image.id,
            "filename": image.filename,
            "original_filename": image.original_filename,
            "file_size": image.file_size,
            "mime_type": image.mime_type,
            "user_id": image.user_id,
            "product_id": image.product_id,
            "description": image.description,
            "created_at": image.created_at.isoformat() if image.created_at else None,
            "updated_at": image.updated_at.isoformat() if image.updated_at else None,
            "download_url": f"/image/{image.id}",
            "view_url": f"/image-view/{image.id}"
        }
    finally:
        db.close()


@app.get("/user-images/{user_id}")
async def get_user_images(user_id: int):
    """Get all images for a specific user"""
    db = Session()
    try:
        images = db.query(Image).filter(Image.user_id == user_id).all()
        
        return {
            "user_id": user_id,
            "total_images": len(images),
            "images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "original_filename": img.original_filename,
                    "file_size": img.file_size,
                    "mime_type": img.mime_type,
                    "description": img.description,
                    "created_at": img.created_at.isoformat() if img.created_at else None,
                    "view_url": f"/image-view/{img.id}"
                }
                for img in images
            ]
        }
    finally:
        db.close()


@app.get("/product-images/{product_id}")
async def get_product_images(product_id: str):
    """Get all images for a specific product"""
    db = Session()
    try:
        images = db.query(Image).filter(Image.product_id == product_id).all()
        
        return {
            "product_id": product_id,
            "total_images": len(images),
            "images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "original_filename": img.original_filename,
                    "file_size": img.file_size,
                    "mime_type": img.mime_type,
                    "description": img.description,
                    "created_at": img.created_at.isoformat() if img.created_at else None,
                    "view_url": f"/image-view/{img.id}"
                }
                for img in images
            ]
        }
    finally:
        db.close()


@app.delete("/image/{image_id}")
async def delete_image(image_id: int):
    """Delete an image"""
    db = Session()
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete file from disk
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        
        # Delete record from database
        db.delete(image)
        db.commit()
        
        return {
            "message": "Image deleted successfully",
            "image_id": image_id,
            "filename": image.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Image deletion failed: {str(e)}")
    finally:
        db.close()


# Get batch uploads with calculated totals
@app.get('/batch-uploads')
def get_batch_uploads(user_id: int = None):
    """Get all batch uploads with calculated totals from product_1 table"""
    db = Session()
    try:
        print(f"[BATCH_UPLOADS] Fetching batch uploads for user_id: {user_id}")
        
        # Build query
        query = db.query(BatchUpload)
        
        # Filter by user_id if provided
        if user_id:
            query = query.filter(BatchUpload.user_id == user_id)
        
        # Get batch uploads
        batches = query.order_by(BatchUpload.upload_date.desc()).all()
        print(f"[BATCH_UPLOADS] Found {len(batches)} batches")
        
        # Calculate totals for each batch
        batch_list = []
        for batch in batches:
            try:
                # Get products in this batch
                products_in_batch = db.query(Product).filter(
                    Product.batch_id == batch.id
                ).all()
                
                # Calculate totals
                total_amount = sum(p.CRAMOUNT for p in products_in_batch if p.CRAMOUNT)
                total_rows = len(products_in_batch)
                
                # Format upload date
                upload_date_str = batch.upload_date.strftime('%d/%m/%Y %H:%M:%S') if batch.upload_date else '-'
                
                batch_data = {
                    "id": batch.id,
                    "user_id": batch.user_id,
                    "batch_name": batch.batch_name,
                    "upload_date": upload_date_str,
                    "total_rows": total_rows or batch.total_rows,
                    "total_amount": total_amount or batch.total_amount,
                    "disbursed_amount": batch.disbursed_amount or 0.0,
                    "status": batch.status
                }
                batch_list.append(batch_data)
                print(f"[BATCH_UPLOADS] Batch {batch.id}: {batch.batch_name} - {total_rows} rows, ৳{total_amount}")
            except Exception as batch_error:
                print(f"[BATCH_UPLOADS] Error processing batch {batch.id}: {str(batch_error)}")
                raise
        
        print(f"[BATCH_UPLOADS] Returning {len(batch_list)} batches")
        return batch_list
    except Exception as e:
        print(f"[BATCH_UPLOADS] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch batch uploads: {str(e)}")
    finally:
        db.close()


# Create batch upload record
@app.post('/batch-uploads')
def create_batch_upload(batch_data: dict, user_id: int = None):
    """Create a new batch upload record"""
    db = Session()
    try:
        from dbmodel import BatchUpload
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Create batch upload record
        db_batch = BatchUpload(
            user_id=user_id,
            batch_name=batch_data.get('batch_name', f'Batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            upload_date=datetime.now(),
            total_rows=batch_data.get('total_rows', 0),
            total_amount=batch_data.get('total_amount', 0.0),
            disbursed_amount=batch_data.get('disbursed_amount', 0.0),
            status=batch_data.get('status', 'Pending')
        )
        
        db.add(db_batch)
        db.commit()
        db.refresh(db_batch)
        
        return {
            "message": "Batch upload created successfully",
            "batch_id": db_batch.id,
            "batch_name": db_batch.batch_name
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create batch upload: {str(e)}")
    finally:
        db.close()


# Login Audit Endpoints
@app.get('/login-audit/recent')
async def get_recent_login_audit(limit: int = 50):
    """Get recent login attempts (successful and failed)"""
    try:
        logins = LoginAuditManager.get_recent_logins(limit=limit)
        return {
            "status": "success",
            "count": len(logins),
            "data": logins
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch login audit: {str(e)}")


@app.get('/login-audit/user/{user_id}')
async def get_user_login_history(user_id: int, limit: int = 50):
    """Get login history for a specific user"""
    try:
        db = Session()
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        history = LoginAuditManager.get_user_login_history(user_id=user_id, limit=limit)
        return {
            "status": "success",
            "user_id": user_id,
            "username": user.username,
            "count": len(history),
            "data": history
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch user login history: {str(e)}")


@app.get('/login-audit/failed')
async def get_failed_login_attempts(limit: int = 50):
    """Get failed login attempts"""
    try:
        failed_logins = LoginAuditManager.get_failed_login_attempts(limit=limit)
        return {
            "status": "success",
            "count": len(failed_logins),
            "data": failed_logins
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch failed login attempts: {str(e)}")


@app.get('/login-audit/stats')
async def get_login_statistics(days: int = 7):
    """Get login statistics for a period"""
    try:
        stats = LoginAuditManager.get_login_stats(days=days)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch login statistics: {str(e)}")


@app.get('/login-audit/suspicious')
async def get_suspicious_activity(threshold_minutes: int = 5):
    """Get suspicious activity (multiple failed logins from same IP)"""
    try:
        suspicious = LoginAuditManager.get_suspicious_activity(threshold_minutes=threshold_minutes)
        return {
            "status": "success",
            "count": len(suspicious),
            "threshold_minutes": threshold_minutes,
            "data": suspicious
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch suspicious activity: {str(e)}")


@app.post('/login-audit/logout')
async def record_logout(logout_data: dict):
    """Record a logout event"""
    try:
        session_id = logout_data.get('session_id')
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        print(f"[LOGOUT] Recording logout for session: {session_id}")
        success = LoginAuditManager.log_logout(session_id=session_id)
        if not success:
            print(f"[LOGOUT] Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        print(f"[LOGOUT] Logout recorded successfully for session: {session_id}")
        return {
            "status": "success",
            "message": "Logout recorded successfully",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LOGOUT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to record logout: {str(e)}")


# ==================== AUDIT LOG ENDPOINTS ====================

@app.get('/audit-logs')
async def get_audit_logs(
    table: str = None,
    operation: str = None,
    limit: int = 50
):
    """Get audit logs with optional filtering"""
    try:
        # Get all logs
        all_logs = AuditLogManager.get_recent_changes(table_name=table, limit=limit)
        
        # Filter by operation if provided
        if operation:
            all_logs = [log for log in all_logs if log['operation'] == operation]
        
        return all_logs
    except Exception as e:
        print(f"[AUDIT_LOG] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to fetch audit logs: {str(e)}")


@app.get('/audit-logs/record/{table}/{record_id}')
async def get_record_changes(table: str, record_id: str):
    """Get all changes for a specific record"""
    try:
        changes = AuditLogManager.get_changes_for_record(table_name=table, record_id=record_id)
        return {
            "status": "success",
            "table": table,
            "record_id": record_id,
            "changes": changes
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch record changes: {str(e)}")


@app.get('/audit-logs/employee/{employee_id}')
async def get_employee_changes(employee_id: str, limit: int = 50):
    """Get all changes made by a specific employee"""
    try:
        changes = AuditLogManager.get_changes_by_employee(employee_id=employee_id, limit=limit)
        return {
            "status": "success",
            "employee_id": employee_id,
            "changes": changes
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch employee changes: {str(e)}")


# Mount static files (frontend) - MUST be last so API routes take precedence
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

