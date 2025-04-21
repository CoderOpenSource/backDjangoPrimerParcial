from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.utils import timezone

class Usuario(AbstractUser):
    ci = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    celular = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_ingreso = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=False)
    foto_perfil = CloudinaryField('image', blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    # Nuevos campos para verificación por correo
    codigo_verificacion = models.CharField(max_length=6, blank=True, null=True)
    expiracion_codigo = models.DateTimeField(blank=True, null=True)

    # 🔥 Token FCM para notificaciones push
    fcm_token = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"

    @property
    def rol(self):
        return self.groups.first().name if self.groups.exists() else "Sin rol"

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Bitacora(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bitacoras'
    )
    accion = models.CharField(max_length=255)
    modulo = models.CharField(max_length=100, blank=True, null=True)  # nuevo
    detalle = models.TextField(blank=True, null=True)  # nuevo
    objeto_afectado = models.CharField(max_length=255, blank=True, null=True)  # nuevo
    referencia_id = models.CharField(max_length=50, blank=True, null=True)  # nuevo
    ip_origen = models.GenericIPAddressField(blank=True, null=True)  # opcional
    dispositivo = models.CharField(max_length=50, blank=True, null=True)  # "web", "móvil", etc.
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.accion} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'
        ordering = ['-fecha']

