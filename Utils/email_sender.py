import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def send_email(subject, recipient, html_content):
    """Función para enviar correos usando smtplib."""
    remitente = os.getenv('MAIL_USERNAME')
    contraseña = os.getenv('MAIL_PASSWORD')

    # Configuración del correo
    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = recipient
    msg["Subject"] = subject

    # Adjuntar el contenido HTML
    msg.attach(MIMEText(html_content, "html"))

    # Conectar al servidor SMTP
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)  # Cambia a SSL
        server.login(remitente, contraseña)
        server.sendmail(remitente, recipient, msg.as_string())
        server.quit()
        print("Correo enviado exitosamente")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

