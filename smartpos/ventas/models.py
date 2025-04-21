from django.db import models
from django.contrib.auth import get_user_model
from productos.models import Producto
from cloudinary.models import CloudinaryField
User = get_user_model()


# 2. Tipos de Pago (Visa, Mastercard, etc.)


class TipoPago(models.Model):
    nombre = models.CharField(max_length=50)
    imagen = CloudinaryField('imagen', blank=True, null=True)

    def __str__(self):
        return self.nombre


class Carrito(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('confirmado', 'Confirmado'),
        ('abandonado', 'Abandonado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carritos')  # 🔁 ya no OneToOne
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    total_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"Carrito de {self.usuario} - {self.estado}"


# 4. Ítems del Carrito
class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('carrito', 'producto')

# 5. Venta (pedido confirmado)
class Venta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_pago = models.ForeignKey(TipoPago, on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('fallido', 'Fallido'),
    ], default='pendiente')
    referencia_pago = models.CharField(max_length=100, blank=True, null=True)

# 6. Detalle de Venta (productos vendidos)
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='detalles_venta')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

from django.db import models

class Factura(models.Model):
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    archivo_pdf_url = models.URLField()  # ruta en Cloudinary, S3, etc.
    enviado_por_correo = models.BooleanField(default=False)

    def __str__(self):
        return f'Factura #{self.numero_factura} - {self.venta.usuario}'


# 7. Comandos de voz capturados
class ComandoVoz(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto_original = models.TextField()
    interpretacion = models.TextField(blank=True, null=True)
    accion_sugerida = models.CharField(max_length=100, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

class CampañaDescuento(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio.date()} - {self.fecha_fin.date()})"


class Descuento(models.Model):
    campaña = models.ForeignKey(
        CampañaDescuento,
        on_delete=models.CASCADE,
        related_name='descuentos'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='descuentos'  # ✅ agregado
    )
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('campaña', 'producto')

    def __str__(self):
        return f"{self.porcentaje}% en {self.producto.nombre} - Campaña: {self.campaña.nombre}"
