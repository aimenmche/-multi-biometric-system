from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., max_length=100)
    role: str = "student"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BiometricRegister(BaseModel):
    user_id: int
    biometric_type: str  # "face" or "fingerprint"
    template_data: str


class BiometricLogin(BaseModel):
    biometric_type: str
    template_data: str


class AttendanceRecord(BaseModel):
    user_id: int
    method: str
    status: str = "present"


class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    timestamp: Optional[datetime] = None
    method: str
    status: str

    class Config:
        from_attributes = True


class AdminActionCreate(BaseModel):
    action: str
    target_user_id: Optional[int] = None
    details: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class AttendanceListResponse(BaseModel):
    records: List[AttendanceResponse]
    total: int
