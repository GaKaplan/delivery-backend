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

    def _get_smtp_server(self):
        smtp_host = self.config.get("smtp_host", "").strip()
        smtp_port = self.config.get("smtp_port", "587").strip()
        smtp_user = self.config.get("smtp_user", "").strip()
        smtp_pass = self.config.get("smtp_password", "").strip()
        smtp_tls = self.config.get("smtp_tls", "True").lower() == "true"

        if not all([smtp_host, smtp_user, smtp_pass]):
            return None, "Configuración SMTP incompleta (Faltan host, usuario o contraseña)."

        try:
            port = int(smtp_port)
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_host, port, timeout=20)
            else:
                server = smtplib.SMTP(smtp_host, port, timeout=20)
                if smtp_tls:
                    server.starttls()
            
            server.login(smtp_user, smtp_pass)
            return server, None
        except socket.timeout:
            return None, f"Tiempo de espera agotado (Timeout) al conectar con {smtp_host}."
        except Exception as e:
            return None, str(e)

    def send_verification_email(self, to_email: str, token: str, username: str):
        # Build verification link
        frontend_url = self.config.get("frontend_url", "https://hojaruta.infotechlatam.com").strip()
        if frontend_url.endswith("/"):
            frontend_url = frontend_url[:-1]
            
        verify_link = f"{frontend_url}/#/verify-email?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = self.config.get("smtp_user")
        msg['To'] = to_email
        msg['Subject'] = "Verifica tu cuenta - Delivery Route Optimizer"

        body = f"""Hola {username},\n\nGracias por registrarte en Delivery Route Optimizer.\nPara activar tu cuenta, por favor haz clic en el siguiente enlace:\n\n{verify_link}\n\nSi no solicitaste esta cuenta, puedes ignorar este mensaje.\n\nAtentamente,\nEl equipo de Soporte."""
        msg.attach(MIMEText(body, 'plain'))

        server, error = self._get_smtp_server()
        if error: return False, error

        try:
            server.send_message(msg)
            server.quit()
            return True, None
        except Exception as e:
            return False, str(e)

    def send_reset_password_email(self, to_email: str, token: str, username: str):
        # Build reset link
        frontend_url = self.config.get("frontend_url", "https://hojaruta.infotechlatam.com").strip()
        if frontend_url.endswith("/"):
            frontend_url = frontend_url[:-1]
            
        reset_link = f"{frontend_url}/#/reset-password?token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = self.config.get("smtp_user")
        msg['To'] = to_email
        msg['Subject'] = "Restablece tu contraseña - Delivery Route Optimizer"

        body = f"""Hola {username},\n\nHas solicitado restablecer tu contraseña en Delivery Route Optimizer.\nPor favor, haz clic en el siguiente enlace para crear una nueva contraseña:\n\n{reset_link}\n\nEste enlace expirará en 1 hora.\n\nSi no solicitaste este cambio, puedes ignorar este mensaje.\n\nAtentamente,\nEl equipo de Soporte."""
        msg.attach(MIMEText(body, 'plain'))

        server, error = self._get_smtp_server()
        if error: return False, error

        try:
            server.send_message(msg)
            server.quit()
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def generate_token():
        import secrets
        return secrets.token_urlsafe(32)
