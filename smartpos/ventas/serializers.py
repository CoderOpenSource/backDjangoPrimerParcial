# tipos_pago/serializers.py
import uuid
from rest_framework import serializers
from usuarios.serializers import UsuarioSerializer

from .models import TipoPago, Carrito, ItemCarrito, Venta, DetalleVenta, Factura
from productos.models import Producto, MovimientoInventario, Stock
from django.db import transaction
from decimal import Decimal
from ventas.utils.pdf_generator import generar_y_subir_pdf  # <--- Importa tu función
from utils.email_utils import enviar_factura_por_correo
from productos.serializers import ProductoSerializer
from ventas.utils.notificaciones import enviar_notificacion_stock_bajo
class TipoPagoSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(required=False, allow_null=True, write_only=True)
    imagen_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TipoPago
        fields = '__all__'

    def get_imagen_url(self, obj):
        return obj.imagen.url if obj.imagen else None

class CarritoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'usuario_nombre', 'fecha_actualizacion', 'estado', 'total_estimado']

class ItemCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), write_only=True, source='producto'
    )

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto', 'producto_id', 'cantidad']

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        producto = validated_data['producto']
        cantidad = validated_data['cantidad']

        try:
            stock = producto.stock.cantidad_actual
        except Stock.DoesNotExist:
            raise serializers.ValidationError({
                "detalle": "Este producto no tiene stock registrado."
            })

        if cantidad > stock:
            raise serializers.ValidationError({
                "detalle": f"Solo hay {stock} unidades disponibles."
            })

        with transaction.atomic():
            carrito, created = Carrito.objects.get_or_create(
                usuario=user,
                estado='activo',
                defaults={'total_estimado': 0}
            )

            item, created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                defaults={'cantidad': cantidad}
            )
            if not created:
                total_cantidad = item.cantidad + cantidad
                if total_cantidad > stock:
                    raise serializers.ValidationError({
                        "detalle": f"Solo hay {stock} unidades disponibles. Ya tienes {item.cantidad} en tu carrito."
                    })
                item.cantidad = total_cantidad
                item.save()

            # ✅ Aplicar descuento si existe
            precio_final = producto.get_precio_con_descuento()
            print(precio_final)
            carrito.total_estimado += Decimal(str(precio_final)) * cantidad
            carrito.save()

        return item

    def update(self, instance, validated_data):
        nueva_cantidad = validated_data.get('cantidad', instance.cantidad)
        producto = instance.producto

        try:
            stock = producto.stock.cantidad_actual
        except Stock.DoesNotExist:
            raise serializers.ValidationError({
                "detalle": "Este producto no tiene stock registrado."
            })

        if nueva_cantidad > stock:
            raise serializers.ValidationError({
                "detalle": f"Solo hay {stock} unidades disponibles."
            })

        with transaction.atomic():
            # Restar el total anterior del carrito
            precio_unitario = producto.get_precio_con_descuento()
            carrito = instance.carrito
            carrito.total_estimado -= Decimal(str(precio_unitario)) * instance.cantidad

            # Actualizar la cantidad
            instance.cantidad = nueva_cantidad
            instance.save()

            # Sumar el nuevo total
            carrito.total_estimado += Decimal(str(precio_unitario)) * nueva_cantidad
            carrito.save()

        return instance


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'cantidad', 'precio_unitario']

class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = ['numero_factura', 'fecha_emision', 'archivo_pdf_url', 'enviado_por_correo']
class VentaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)  # ✅ Añadido aquí
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    factura = FacturaSerializer(read_only=True)
    tipo_pago = TipoPagoSerializer(read_only=True)
    tipo_pago_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoPago.objects.all(), source='tipo_pago', write_only=True
    )
    referencia_pago = serializers.CharField(required=False)

    class Meta:
        model = Venta
        fields = [
            'id', 'usuario', 'fecha_venta', 'total',
            'tipo_pago', 'tipo_pago_id', 'estado', 'referencia_pago',
            'detalles', 'factura'
        ]
        read_only_fields = ['usuario', 'total', 'estado', 'fecha_venta', 'tipo_pago', 'detalles', 'factura']

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        tipo_pago = validated_data['tipo_pago']
        referencia = validated_data.get('referencia_pago', None)

        with transaction.atomic():
            # Obtener carrito activo
            carrito = Carrito.objects.filter(usuario=user, estado='activo').first()
            if not carrito:
                raise serializers.ValidationError("No hay carrito activo.")

            # Validar stock antes de continuar
            errores_stock = []
            for item in carrito.items.all():
                stock_actual = item.producto.stock.cantidad_actual
                if stock_actual < item.cantidad:
                    errores_stock.append(
                        f"El producto '{item.producto.nombre}' solo tiene {stock_actual} unidades disponibles."
                    )

            if errores_stock:
                raise serializers.ValidationError({"stock": errores_stock})

            # Crear venta
            venta = Venta.objects.create(
                usuario=user,
                tipo_pago=tipo_pago,
                total=carrito.total_estimado,
                referencia_pago=referencia,
                estado='pagado' if referencia else 'pendiente'
            )

            # Crear detalles y descontar stock
            for item in carrito.items.all():
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio_unitario
                )

                stock = item.producto.stock
                stock.cantidad_actual -= item.cantidad
                stock.save()

                # Enviar notificación si stock está en nivel crítico
                if stock.cantidad_actual <= stock.punto_reorden:
                    enviar_notificacion_stock_bajo(item.producto)

                MovimientoInventario.objects.create(
                    producto=item.producto,
                    tipo='salida',
                    cantidad=item.cantidad,
                    descripcion=f"Venta #{venta.id}",
                    usuario=user
                )

            carrito.estado = 'confirmado'
            carrito.save()
            carrito.items.all().delete()

            numero_factura = f"F-{uuid.uuid4().hex[:10].upper()}"
            factura = Factura.objects.create(
                venta=venta,
                numero_factura=numero_factura,
                enviado_por_correo=False
            )

            url_pdf = generar_y_subir_pdf(venta, factura)
            factura.archivo_pdf_url = url_pdf
            factura.save()

            enviar_factura_por_correo(
                destinatario=user.email,
                nombre_cliente=user.get_full_name(),
                numero_factura=factura.numero_factura,
                url_pdf=url_pdf
            )
            factura.enviado_por_correo = True
            factura.save()
            return venta


from .models import CampañaDescuento, Descuento
from productos.serializers import ProductoSerializer

class CampañaDescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampañaDescuento
        fields = '__all__'

from .models import CampañaDescuento
from productos.serializers import ProductoSerializer

class DescuentoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source='producto', write_only=True
    )

    campana = CampañaDescuentoSerializer(read_only=True, source='campaña')  # 👈 rename output field
    campana_id = serializers.PrimaryKeyRelatedField(
        queryset=CampañaDescuento.objects.all(), source='campaña', write_only=True
    )

    class Meta:
        model = Descuento
        fields = ['id', 'campana', 'campana_id', 'producto', 'producto_id', 'porcentaje', 'activo']

class CarritoConItemsSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Carrito
        fields = [
            'id',
            'usuario',
            'username',
            'usuario_nombre',
            'fecha_actualizacion',
            'estado',
            'total_estimado',
            'items'
        ]

    def get_items(self, obj):
        from .serializers import ItemCarritoSerializer
        return ItemCarritoSerializer(obj.items.all(), many=True, context=self.context).data
