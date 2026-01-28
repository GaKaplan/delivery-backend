from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    role: str = "user"
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: int = 0  # 0=Pending, 1=Active

class UserCreate(UserBase):
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[int] = None


class User(UserBase):
    id: int


    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str
