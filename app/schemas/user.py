from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"
    parent = "parent"

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: RoleEnum

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    role: Optional[RoleEnum]
    password: Optional[str]

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True  # Updated from orm_mode
        # If using Pydantic v2, 'from_attributes' replaces 'orm_mode'

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
