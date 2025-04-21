from firebase_admin import messaging
from usuarios.models import Usuario
from notificaciones.models import Notificacion
from firebase import firebase_config  # Asegura la inicialización
from django.utils.timezone import localtime


# 📦 Notificación por stock bajo
def enviar_notificacion_stock_bajo(producto):
    titulo = f"⚠️ Stock Bajo: {producto.nombre}"
    cuerpo = f"El stock actual es {producto.stock.cantidad_actual} y el punto de reorden es {producto.stock.punto_reorden}."

    administradores = Usuario.objects.filter(
        is_active=True,
        fcm_token__isnull=False,
        groups__name='Administrador'
    )

    for admin in administradores:
        Notificacion.objects.create(
            usuario=admin,
            titulo=titulo,
            mensaje=cuerpo
        )

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo
                ),
                token=admin.fcm_token
            )
            messaging.send(message)
        except Exception as e:
            print(f"❌ Error al enviar notificación a {admin.username}: {e}")


# 🎯 Notificación por campaña de descuento activa
def enviar_notificacion_campaña_activa(campaña):
    titulo = f"🎉 ¡Nueva Campaña Activa!"

    fecha_inicio = localtime(campaña.fecha_inicio).strftime('%d/%m/%Y %H:%M')
    fecha_fin = localtime(campaña.fecha_fin).strftime('%d/%m/%Y %H:%M')

    mensaje = (
        f"Desde el {fecha_inicio} hasta el {fecha_fin}, "
        f"la campaña '{campaña.nombre}' estará activa. "
        f"¡Aprovecha los descuentos disponibles por tiempo limitado!"
    )

    clientes = Usuario.objects.filter(
        is_active=True,
        groups__name='Cliente'
    )

    for cliente in clientes:
        Notificacion.objects.create(
            usuario=cliente,
            titulo=titulo,
            mensaje=mensaje
        )

        if cliente.fcm_token:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=titulo,
                        body=mensaje
                    ),
                    token=cliente.fcm_token
                )
                print("NOTIFICACION ENVIADA")
                messaging.send(message)
            except Exception as e:
                print(f"❌ Error al enviar notificación a {cliente.username}: {e}")
