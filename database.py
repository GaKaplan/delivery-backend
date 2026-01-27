import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL:
    print(f"DATABASE: Conectando a base de datos externa... {SQLALCHEMY_DATABASE_URL.split('@')[-1]}")
else:
    print("WARNING: No se encontró DATABASE_URL. Usando fallback local (localhost).")
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/delivery_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
