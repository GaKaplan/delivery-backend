from sqlalchemy import Column, Integer, String, Enum
from database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER, nullable=False)
    
    # New Profile Fields (V3.0)
    full_name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Integer, default=0, nullable=False) # 0=Pending, 1=Active
    
    # Email Verification Fields (V3.1)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(100), nullable=True)

class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)


