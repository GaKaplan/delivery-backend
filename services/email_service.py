import smtplib
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
        smtp_host = self.config.get("smtp_host")
        smtp_port = self.config.get("smtp_port")
        smtp_user = self.config.get("smtp_user")
        smtp_pass = self.config.get("smtp_password")
        smtp_tls = self.config.get("smtp_tls", "True").lower() == "true"

        if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
            logger.error("Configuración SMTP incompleta. No se pudo enviar el correo.")
            return False

        # Build verification link (This should ideally come from another config but we'll use a relative path or a known public URL)
        # For now, let's assume the frontend will handle the verification route
        verify_link = f"https://hojaruta.infotechlatam.com/verify-email?token={token}"
        
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
            # Port 465 is for Implicit SSL
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_host, port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, port, timeout=15)
                if smtp_tls:
                    server.starttls()
            
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email de verificación enviado a {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            return False

    @staticmethod
    def generate_token():
        import secrets
        return secrets.token_urlsafe(32)
