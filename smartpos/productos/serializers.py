from rest_framework import serializers
from .models import Categoria, Subcategoria, Producto, ImagenProducto, Stock, MovimientoInventario
import json
from django.utils import timezone


class CategoriaSerializer(serializers.ModelSerializer):
    foto_perfil = serializers.ImageField(required=False, allow_null=True, write_only=True)
    foto_perfil_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Categoria
        fields = '__all__'

    def get_foto_perfil_url(self, obj):
        return obj.foto_perfil.url if obj.foto_perfil else None


class SubcategoriaSerializer(serializers.ModelSerializer):
    foto_perfil = serializers.ImageField(required=False, allow_null=True, write_only=True)
    foto_perfil_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subcategoria
        fields = '__all__'

    def get_foto_perfil_url(self, obj):
        return obj.foto_perfil.url if obj.foto_perfil else None


class ImagenProductoSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ImagenProducto
        fields = ['id', 'imagen', 'imagen_url', 'descripcion', 'orden']

    def get_imagen_url(self, obj):
        return obj.imagen.url if obj.imagen else None


class ProductoSerializer(serializers.ModelSerializer):
    imagenes = ImagenProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'codigo_barra', 'precio_unitario',
            'unidad_medida', 'subcategoria', 'estado', 'imagenes'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        imagenes_meta = request.data.get('imagenes_meta')
        print("📥 Datos recibidos para crear producto:", request.data)
        print("📂 Archivos:", request.FILES)

        producto = Producto.objects.create(**validated_data)

        if imagenes_meta:
            imagenes_meta = json.loads(imagenes_meta)
            print("🖼️ Procesando metadatos de imágenes:", imagenes_meta)
            for meta in imagenes_meta:
                file_key = meta.get('file_key')
                imagen = request.FILES.get(file_key)
                if imagen:
                    ImagenProducto.objects.create(
                        producto=producto,
                        imagen=imagen,
                        descripcion=meta.get('descripcion', ''),
                        orden=meta.get('orden', 0)
                    )
                    print(f"✅ Imagen subida con clave {file_key}")
                else:
                    print(f"⚠️ Imagen no encontrada para la clave {file_key}")

        return producto

    def update(self, instance, validated_data):
        request = self.context.get('request')
        imagenes_meta = request.data.get('imagenes_meta')
        imagenes_eliminadas = request.data.get('imagenes_eliminadas')

        print("🔄 Actualizando producto:", request.data)
        print("📂 Archivos recibidos:", request.FILES)

        # Actualiza los campos básicos del producto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ✅ Eliminar imágenes por ID si se especifican
        if imagenes_eliminadas:
            ids_eliminar = json.loads(imagenes_eliminadas)
            print("🗑️ IDs de imágenes a eliminar:", ids_eliminar)
            ImagenProducto.objects.filter(id__in=ids_eliminar, producto=instance).delete()

        # ✅ Procesar nuevas imágenes (no borrar todas como antes)
        if imagenes_meta:
            imagenes_meta = json.loads(imagenes_meta)
            for meta in imagenes_meta:
                file_key = meta.get('file_key')
                imagen = request.FILES.get(file_key)
                if imagen:
                    ImagenProducto.objects.create(
                        producto=instance,
                        imagen=imagen,
                        descripcion=meta.get('descripcion', ''),
                        orden=meta.get('orden', 0)
                    )
                    print(f"🆕 Imagen añadida con clave {file_key}")
                else:
                    print(f"⚠️ No se encontró archivo para clave: {file_key}")

        return instance

class StockSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Stock
        fields = ['id', 'producto', 'producto_nombre', 'cantidad_actual', 'punto_reorden', 'fecha_actualizacion']
        read_only_fields = ['fecha_actualizacion']


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = ['id', 'producto', 'producto_nombre', 'tipo', 'cantidad', 'descripcion', 'fecha_movimiento', 'usuario']
        read_only_fields = ['fecha_movimiento', 'usuario']

    def validate(self, data):
        tipo = data.get('tipo')
        cantidad = data.get('cantidad')
        producto = data.get('producto')

        # Validar stock suficiente si es salida
        if tipo == 'salida':
            try:
                stock = Stock.objects.get(producto=producto)
            except Stock.DoesNotExist:
                raise serializers.ValidationError("No hay stock registrado para este producto.")
            if stock.cantidad_actual < cantidad:
                raise serializers.ValidationError("Cantidad insuficiente en stock para realizar la salida.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        producto = validated_data['producto']
        tipo = validated_data['tipo']
        cantidad = validated_data['cantidad']

        # Obtener o crear stock
        stock, _ = Stock.objects.get_or_create(producto=producto)

        # Actualizar stock según el tipo de movimiento
        if tipo == 'entrada':
            stock.cantidad_actual += cantidad
        elif tipo == 'salida':
            stock.cantidad_actual -= cantidad

        stock.fecha_actualizacion = timezone.now()
        stock.save()

        # Crear movimiento con usuario
        movimiento = MovimientoInventario.objects.create(
            producto=producto,
            tipo=tipo,
            cantidad=cantidad,
            descripcion=validated_data.get('descripcion', ''),
            usuario=user
        )
        return movimiento