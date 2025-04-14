from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    foto_perfil = CloudinaryField('image', blank=True, null=True)  # 👈 imagen cloud

    def __str__(self):
        return self.nombre


class Subcategoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    estado = models.BooleanField(default=True)
    foto_perfil = CloudinaryField('image', blank=True, null=True)  # 👈 imagen cloud

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"



class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    codigo_barra = models.CharField(max_length=50, unique=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=20)
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, related_name='productos')
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"

    class Meta:
        ordering = ['orden']


class Stock(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name='stock')
    cantidad_actual = models.IntegerField(default=0)
    punto_reorden = models.IntegerField(default=5)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad_actual} unidades"


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [('entrada', 'Entrada'), ('salida', 'Salida')]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"
