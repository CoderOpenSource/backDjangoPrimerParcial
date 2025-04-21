from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
from django.utils import timezone


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


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)
    foto_perfil = CloudinaryField('image', blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    codigo_barra = models.CharField(max_length=50, unique=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unidad_medida = models.CharField(max_length=20)
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, related_name='productos')
    creado_en = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, related_name='productos')

    def __str__(self):
        return self.nombre

    def get_descuento_vigente(self):
        ahora = timezone.now()
        return self.descuentos.filter(
            activo=True,
            campaña__activa=True,
            campaña__fecha_inicio__lte=ahora,
            campaña__fecha_fin__gte=ahora
        ).first()

    def get_precio_con_descuento(self):
        descuento = self.get_descuento_vigente()
        if descuento:
            return self.precio_unitario * (1 - (descuento.porcentaje / 100))
        return self.precio_unitario

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = CloudinaryField('image')  # ✅ Subida automática a Cloudinary
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



class ProductoFavorito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favoritos'  # Puedes acceder como usuario.favoritos
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='favoritos'  # Puedes acceder como producto.favoritos
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'producto')
        verbose_name = 'Producto Favorito'
        verbose_name_plural = 'Productos Favoritos'

    def __str__(self):
        return f"{self.usuario.username} ❤️ {self.producto.nombre}"
