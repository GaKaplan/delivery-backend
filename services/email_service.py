import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from models import Configuration
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self.config = self._load_config()

    def _load_config(self):
        configs = self.db.query(Configuration).all()
        config_dict = {c.key: c.value for c in configs}
        return config_dict

    def send_verification_email(self, to_email: str, token: str, username: str):
        smtp_host = self.config.get("smtp_host", "").strip()
        smtp_port = self.config.get("smtp_port", "587").strip()
        smtp_user = self.config.get("smtp_user", "").strip()
        smtp_pass = self.config.get("smtp_password", "").strip()
        smtp_tls = self.config.get("smtp_tls", "True").lower() == "true"

        if not all([smtp_host, smtp_user, smtp_pass]):
            msg = "Configuración SMTP incompleta (Faltan host, usuario o contraseña)."
            logger.error(msg)
            return False, msg

        # Build verification link
        frontend_url = self.config.get("frontend_url", "https://hojaruta.infotechlatam.com").strip()
        # Remove trailing slash if present
        if frontend_url.endswith("/"):
            frontend_url = frontend_url[:-1]
            
        verify_link = f"{frontend_url}/verify-email?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "Verifica tu cuenta - Delivery Route Optimizer"

        body = f"""
        Hola {username},
        
        Gracias por registrarte en Delivery Route Optimizer.
        Para activar tu cuenta, por favor haz clic en el siguiente enlace:
        
        {verify_link}
        
        Si no solicitaste esta cuenta, puedes ignorar este mensaje.
        
        Atentamente,
        El equipo de Soporte.
        """
        
        msg.attach(MIMEText(body, 'plain'))

        try:
            port = int(smtp_port)
            logger.info(f"SMTP: Intentando conexión a {smtp_host}:{port} (TLS={smtp_tls})")
            
            # 1. Establishment of connection
            if port == 465:
                # Port 465 is typically Implicit SSL
                server = smtplib.SMTP_SSL(smtp_host, port, timeout=20)
            else:
                # Standard ports (587, 25, etc) use STARTTLS if requested
                server = smtplib.SMTP(smtp_host, port, timeout=20)
                if smtp_tls:
                    server.starttls()
            
            # 2. Authentication
            server.login(smtp_user, smtp_pass)
            
            # 3. Send
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email de verificación enviado a {to_email}")
            return True, None
        except socket.timeout:
            error_msg = f"Tiempo de espera agotado (Timeout) al conectar con {smtp_host}. Intente con el puerto 587 si el 465 está bloqueado."
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error al enviar email: {error_msg}")
            # Identify common SSL errors
            if "SSL" in error_msg or "wrong version" in error_msg.lower():
                error_msg += ". Intente cambiar la configuración de TLS o de puerto."
            return False, error_msg

    @staticmethod
    def generate_token():
        import secrets
        return secrets.token_urlsafe(32)
