import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.app_config import app_config


def send_email(to_email: str, subject: str, body: str) -> bool:
    sender_email = app_config.EMAIL_SENDER
    sender_password = app_config.EMAIL_PASSWORD

    if not sender_email or not sender_password:
        error_msg = (
            "Email credentials not set. "
            "Please configure EMAIL_SENDER and EMAIL_PASSWORD."
        )
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        smtp_server = getattr(app_config, "EMAIL_SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(getattr(app_config, "EMAIL_SMTP_PORT", 587))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        return True

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        raise RuntimeError("Failed to send email") from e
