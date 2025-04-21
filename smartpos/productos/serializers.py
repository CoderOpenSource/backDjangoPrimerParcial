from rest_framework import serializers
from .models import Categoria, Subcategoria, Producto, ImagenProducto, Stock, MovimientoInventario, ProductoFavorito, Marca
import json
from django.utils import timezone
import random
import string

def generar_codigo_barra_unico():
    while True:
        codigo = ''.join(random.choices(string.digits, k=13))  # código de 13 dígitos
        if not Producto.objects.filter(codigo_barra=codigo).exists():
            return codigo

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

class MarcaSerializer(serializers.ModelSerializer):
    foto_perfil = serializers.ImageField(required=False, allow_null=True, write_only=True)
    foto_perfil_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'estado', 'foto_perfil', 'foto_perfil_url', 'creado_en', 'actualizado_en']

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
    subcategoria = SubcategoriaSerializer(read_only=True)
    marca = MarcaSerializer(read_only=True)
    categoria_nombre = serializers.SerializerMethodField(read_only=True)
    cantidad_stock = serializers.SerializerMethodField(read_only=True)
    precio_con_descuento = serializers.SerializerMethodField(read_only=True)
    porcentaje_descuento = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'codigo_barra', 'precio_unitario', 'precio_compra',
            'unidad_medida', 'subcategoria', 'marca', 'estado', 'imagenes',
            'categoria_nombre', 'cantidad_stock',
            'precio_con_descuento', 'porcentaje_descuento'
        ]
        extra_kwargs = {
            'codigo_barra': {'required': False}
        }

    def get_categoria_nombre(self, obj):
        return obj.subcategoria.categoria.nombre if obj.subcategoria and obj.subcategoria.categoria else None

    def get_cantidad_stock(self, obj):
        try:
            return obj.stock.cantidad_actual  # ✅ Usa la relación OneToOne
        except Stock.DoesNotExist:
            return 0  # Si no existe stock, devuelve 0

    def get_precio_con_descuento(self, obj):
        return float(obj.get_precio_con_descuento())

    def get_porcentaje_descuento(self, obj):
        descuento = obj.get_descuento_vigente()
        return float(descuento.porcentaje) if descuento else None

    def _get_descuento_vigente(self, obj):
        ahora = timezone.now()
        return obj.descuentos.filter(
            activo=True,
            campaña__activa=True,
            campaña__fecha_inicio__lte=ahora,
            campaña__fecha_fin__gte=ahora
        ).first()

    def create(self, validated_data):
        request = self.context.get('request')
        imagenes_meta = request.data.get('imagenes_meta')

        # Reemplazar el código de barras por uno nuevo generado
        validated_data['codigo_barra'] = generar_codigo_barra_unico()

        # Establecer relaciones por ID
        subcategoria_id = request.data.get('subcategoria')
        marca_id = request.data.get('marca')

        validated_data['subcategoria_id'] = subcategoria_id
        validated_data['marca_id'] = marca_id

        producto = Producto.objects.create(**validated_data)

        if imagenes_meta:
            imagenes_meta = json.loads(imagenes_meta)
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

        return producto

    def update(self, instance, validated_data):
        request = self.context.get('request')
        imagenes_meta = request.data.get('imagenes_meta')
        imagenes_eliminadas = request.data.get('imagenes_eliminadas')

        # Actualizar atributos básicos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Actualizar relaciones foráneas
        instance.subcategoria_id = request.data.get('subcategoria')
        instance.marca_id = request.data.get('marca')

        instance.save()

        # Eliminar imágenes si se indicaron
        if imagenes_eliminadas:
            ids_eliminar = json.loads(imagenes_eliminadas)
            ImagenProducto.objects.filter(id__in=ids_eliminar, producto=instance).delete()

        # Agregar nuevas imágenes si las hay
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

        return instance

    def update(self, instance, validated_data):
        request = self.context.get('request')
        imagenes_meta = request.data.get('imagenes_meta')
        imagenes_eliminadas = request.data.get('imagenes_eliminadas')

        print("🔄 Actualizando producto:", request.data)
        print("📂 Archivos recibidos:", request.FILES)

        # 🔎 Verifica si 'marca' viene en el request
        print("🏷️ Marca recibida:", request.data.get('marca'))
        print("📂 Subcategoría recibida:", request.data.get('subcategoria'))

        # Actualiza los campos básicos del producto
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Asegura que relaciones foráneas se actualicen correctamente
        instance.marca_id = request.data.get('marca')
        instance.subcategoria_id = request.data.get('subcategoria')

        instance.save()

        # ✅ Eliminar imágenes por ID si se especifican
        if imagenes_eliminadas:
            ids_eliminar = json.loads(imagenes_eliminadas)
            print("🗑️ IDs de imágenes a eliminar:", ids_eliminar)
            ImagenProducto.objects.filter(id__in=ids_eliminar, producto=instance).delete()

        # ✅ Procesar nuevas imágenes
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

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        producto = validated_data['producto']
        cantidad = validated_data['cantidad_actual']
        punto_reorden = validated_data.get('punto_reorden', 5)

        # Verificar si ya existe stock para ese producto
        stock, creado = Stock.objects.get_or_create(producto=producto, defaults={
            'cantidad_actual': 0,
            'punto_reorden': punto_reorden
        })

        if not creado:
            # Ya existe → actualizar stock
            stock.cantidad_actual += cantidad
            stock.punto_reorden = punto_reorden
            stock.fecha_actualizacion = timezone.now()
            stock.save()

            # ✅ Activar producto si estaba inactivo
            producto.estado = True
            producto.save()

            # Registrar movimiento
            MovimientoInventario.objects.create(
                producto=producto,
                tipo='entrada',
                cantidad=cantidad,
                descripcion='Actualización de stock',
                usuario=user
            )

            return stock  # ⚠️ RETORNAR AQUÍ evita que DRF intente crear duplicado

        # Si es nuevo → se configura normalmente
        stock.cantidad_actual = cantidad
        stock.fecha_actualizacion = timezone.now()
        stock.save()

        MovimientoInventario.objects.create(
            producto=producto,
            tipo='entrada',
            cantidad=cantidad,
            descripcion='Registro inicial de stock',
            usuario=user
        )

        return stock


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

class ProductoFavoritoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source='producto', write_only=True
    )

    class Meta:
        model = ProductoFavorito
        fields = ['id', 'usuario', 'producto', 'producto_id', 'fecha_agregado']
        read_only_fields = ['usuario', 'fecha_agregado']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)

