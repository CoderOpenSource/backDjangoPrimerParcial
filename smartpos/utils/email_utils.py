# email_utils.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import string
from django.utils import timezone

# Configuración SMTP
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_HOST_USER = 'samuel.inge.profe@gmail.com'
EMAIL_HOST_PASSWORD = 'cswjgjubqzzeqgng'  # Contraseña de aplicación (sin espacios)


def generar_codigo_verificacion(longitud=6):
    return ''.join(random.choices(string.digits, k=longitud))

def enviar_codigo_verificacion(destinatario, codigo):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = destinatario
        msg['Subject'] = 'Código de Verificación - SmartCart'

        mensaje_html = f"""
        <html>
          <head>
            <style>
              body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f7fa;
                padding: 20px;
                color: #333;
              }}
              .container {{
                background-color: #fff;
                max-width: 600px;
                margin: auto;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
              }}
              .header {{
                text-align: center;
                margin-bottom: 30px;
              }}
              .header h2 {{
                color: #476DFF;
                margin-bottom: 0;
              }}
              .code {{
                font-size: 36px;
                font-weight: bold;
                color: #476DFF;
                text-align: center;
                margin: 20px 0;
              }}
              .footer {{
                margin-top: 30px;
                font-size: 14px;
                color: #777;
                text-align: center;
              }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <img src="https://res.cloudinary.com/dkpuiyovk/image/upload/v1743549971/pngwing.com_36_hkpwth.png" height="60" alt="SmartCart Logo"/>
                <h2>Verifica tu correo</h2>
              </div>
              <p>Hola 👋,</p>
              <p>Gracias por registrarte en <strong>SmartCart</strong>. Para completar tu registro, por favor usa el siguiente código:</p>
              <div class="code">{codigo}</div>
              <p>Este código es válido solo por <strong>10 minutos</strong>. Si no solicitaste esta verificación, puedes ignorar este mensaje.</p>
              <div class="footer">
                &copy; 2025 SmartCart. Todos los derechos reservados.
              </div>
            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(mensaje_html, 'html'))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("Correo de verificación enviado correctamente")
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False
