import random
import string

def generate_recovery_code():
    """Genera un código único de 6 caracteres alfanuméricos"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))
