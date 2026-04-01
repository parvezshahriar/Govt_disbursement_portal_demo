from sqlalchemy import Column, Integer, String, Float, DateTime, func, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from database import Base
from datetime import datetime


class ClientInfo(Base):
    __tablename__ = 'client_info'
    BENEFICIARY_ID = Column(String, primary_key=True, index=True, unique=True)
    name = Column(String)  # From CRACCOUNTTITLE
    gender = Column(String, nullable=True)
    CRACCOUNTNO = Column(String, unique=True)
    CRACCOUNTTYPE = Column(String)
    CRROUTINGNO = Column(String)
    MOBILE = Column(String, unique=True)
    NID_NO = Column(String, unique=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Product(Base):
    __tablename__ = 'product_1'
    EFTREFNUMBER = Column(String, primary_key=True, index=True, unique=True)
    CRAMOUNT = Column(Float)
    BENEFICIARY_ID = Column(String, ForeignKey('client_info.BENEFICIARY_ID'), index=True)
    MIN_CODE = Column(String)
    DEPT_CODE = Column(String)
    PAYMENT_CYCLE_NAME_EN = Column(String)
    SCHEME_CODE = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    batch_id = Column(Integer, nullable=True, index=True)  # Reference to batch upload


class BatchUpload(Base):
    __tablename__ = 'batch_upload'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    batch_name = Column(String, index=True)
    upload_date = Column(DateTime, default=func.now())
    total_rows = Column(Integer)
    total_amount = Column(Float, default=0.0)
    disbursed_amount = Column(Float, default=0.0)
    status = Column(String, default='Pending')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(String, default='user')
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserInfo(Base):
    __tablename__ = 'user_info'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    employee_id = Column(String, nullable=True)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    office_address = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Image(Base):
    __tablename__ = 'image'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_filename = Column(String)
    file_path = Column(String, index=True)
    file_size = Column(Integer)
    mime_type = Column(String)
    user_id = Column(Integer, nullable=True, index=True)
    product_id = Column(String, nullable=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """
    Audit log table to track all changes to critical tables
    Automatically populated by database triggers
    """
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, index=True)  # Name of the table that was modified
    operation = Column(String, index=True)  # INSERT, UPDATE, DELETE
    record_id = Column(String, index=True)  # Primary key of the modified record
    old_values = Column(JSON, nullable=True)  # Previous values (NULL for INSERT)
    new_values = Column(JSON, nullable=True)  # New values (NULL for DELETE)
    changed_columns = Column(JSON, nullable=True)  # List of columns that changed
    employee_id = Column(String, nullable=True, index=True)  # Employee ID who made the change
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True, index=True)  # User ID from user table
    timestamp = Column(DateTime, default=func.now(), index=True)  # When the change occurred


class LoginAudit(Base):
    """
    Login audit log table to track all user login attempts and activities
    Records successful and failed login attempts
    """
    __tablename__ = 'login_audit'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # User ID (NULL for failed logins)
    username = Column(String, index=True)  # Username attempted
    email = Column(String, nullable=True, index=True)  # User email (if available)
    login_status = Column(String, index=True)  # 'SUCCESS' or 'FAILED'
    failure_reason = Column(String, nullable=True)  # Reason for failed login
    ip_address = Column(String, nullable=True)  # User's IP address
    user_agent = Column(String, nullable=True)  # Browser/client info
    session_id = Column(String, nullable=True, index=True)  # Session identifier
    login_timestamp = Column(DateTime, default=func.now(), index=True)  # When login occurred
    logout_timestamp = Column(DateTime, nullable=True)  # When user logged out
    duration_seconds = Column(Integer, nullable=True)  # Session duration in seconds
    description = Column(Text, nullable=True)  # Additional context
