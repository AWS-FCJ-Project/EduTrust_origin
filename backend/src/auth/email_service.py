import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.app_config import app_config
import logging

def send_email(to_email: str, subject: str, body: str):
    sender_email = app_config.EMAIL_SENDER
    sender_password = app_config.EMAIL_PASSWORD
    
    if not sender_email or not sender_password:
        logging.warning("Email credentials not set. Skipping email sending.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False
