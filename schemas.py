from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    role: str = "user"
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: int = 0  # 0=Pending, 1=Active
    email_verified: bool = False
    verification_token: Optional[str] = None

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

# Config Schemas (V3.1)
class ConfigBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class ConfigCreate(ConfigBase):
    pass

class ConfigSchema(ConfigBase):
    id: int
    class Config:
        from_attributes = True

class EmailConfigUpdate(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    frontend_url: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
