from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class ProductSchema(BaseModel):
    EFTREFNUMBER: str
    CRACCOUNTTITLE: str
    CRACCOUNTTYPE: str
    CRACCOUNTNO: str
    CRROUTINGNO: str
    CRAMOUNT: float
    BENEFICIARY_ID: str
    MOBILE: str
    NID_NO: Optional[str] = None
    MIN_CODE: Optional[str] = None
    DEPT_CODE: Optional[str] = None
    PAYMENT_CYCLE_NAME_EN: Optional[str] = None
    SCHEME_CODE: Optional[str] = None

    class Config:
        from_attributes = True


class BatchUploadRequest(BaseModel):
    """Schema for batch upload of products"""
    rows: List[ProductSchema]
    totalValid: Optional[int] = None
    totalInvalid: Optional[int] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str
    password: str
    email: Optional[str] = None
    role: Optional[str] = 'user'

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user info update"""
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None

    class Config:
        from_attributes = True

class UserInfoCreate(BaseModel):
    """Schema for creating/updating user profile info"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    office_address: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserInfoResponse(BaseModel):
    """Schema for user profile info response"""
    id: int
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    office_address: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    """Schema for image response"""
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    user_id: Optional[int] = None
    product_id: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchUploadResponse(BaseModel):
    """Schema for batch upload history response"""
    id: int
    user_id: int
    batch_name: str
    upload_date: Optional[datetime] = None
    total_rows: int
    total_amount: float
    disbursed_amount: float
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
