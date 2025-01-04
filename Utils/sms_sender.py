import os
from dotenv import load_dotenv
from twilio.rest import Client

# Cargar variables de entorno
load_dotenv()

def send_sms(message, phone_number):
    """Envía un SMS usando Twilio."""
    try:
        account_sid = os.getenv('TWILO_ACCOUNT_SID')
        auth_token = os.getenv('TWILO_TOKEN')
        twilo_phone_number = os.getenv('TWILO_PHONE_NUMBER')

        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            messaging_service_sid='MG94829822e7d210c77e64a9ff78856b94',  # Reemplaza si tienes otro SID
            body=message,
            from_=twilo_phone_number,
            to=phone_number
        )
        print(f"Mensaje enviado con SID: {message.sid}")
    except Exception as e:
        raise ValueError(f"Error al enviar SMS: {str(e)}")
