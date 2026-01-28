import os
import pymysql
from database import SQLALCHEMY_DATABASE_URL

def migrate():
    print(f"Iniciando migración en: {SQLALCHEMY_DATABASE_URL.split('@')[-1]}")
    
    # Parse connection string manually for pymysql
    # mysql+pymysql://user:pass@host:port/db
    clean_url = SQLALCHEMY_DATABASE_URL.replace("mysql+pymysql://", "")
    auth_part, rest = clean_url.split("@")
    user, password = auth_part.split(":")
    host_port, db_name = rest.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 3306

    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port=port
        )
        cursor = conn.cursor()
        
        # Columns to add for V3.1
        columns = [
            ("full_name", "VARCHAR(100)"),
            ("email", "VARCHAR(100)"),
            ("phone", "VARCHAR(20)"),
            ("is_active", "INT DEFAULT 0"),
            ("email_verified", "BOOLEAN DEFAULT FALSE"),
            ("verification_token", "VARCHAR(100)")
        ]
        
        for col_name, col_type in columns:
            try:
                print(f"Agregando columna {col_name}...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Columna {col_name} agregada.")
            except pymysql.err.InternalError as e:
                if e.args[0] == 1060: # Column already exists
                    print(f"La columna {col_name} ya existe. Saltando.")
                else:
                    raise e

        # Create configurations table
        print("Creando tabla configurations si no existe...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                `key` VARCHAR(50) UNIQUE NOT NULL,
                value VARCHAR(255) NOT NULL,
                description VARCHAR(255),
                INDEX ( `key` )
            )
        """)
        print("Tabla configurations lista.")

        # Ensure existing admin is active and verified
        cursor.execute("UPDATE users SET is_active = 1, email_verified = 1 WHERE role = 'admin'")

        
        conn.commit()
        print("Migración completada exitosamente.")
        
    except Exception as e:
        print(f"ERROR en la migración: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
