import firebase_admin
from firebase_admin import credentials
import os

# Ruta absoluta al archivo JSON de credenciales
cred_path = os.path.join(os.path.dirname(__file__), 'smartcart-a04b9-firebase-adminsdk-fbsvc-f6f7dfce23.json')

# Evita inicializar más de una vez
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
