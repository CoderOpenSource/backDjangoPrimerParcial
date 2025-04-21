from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from ventas.pagination import CustomPagination

from .models import TipoPago, Carrito, ItemCarrito, Venta
from .serializers import TipoPagoSerializer, CarritoSerializer, ItemCarritoSerializer, VentaSerializer, CarritoConItemsSerializer
from django.shortcuts import get_object_or_404
from decimal import Decimal
from usuarios.utils.bitacora_utils import registrar_bitacora

class TipoPagoViewSet(viewsets.ModelViewSet):
    queryset = TipoPago.objects.all()
    serializer_class = TipoPagoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        tipo = serializer.save()
        registrar_bitacora(self.request, 'Creó un tipo de pago', modulo='Pagos', objeto_afectado=tipo.nombre)

    def perform_update(self, serializer):
        tipo = serializer.save()
        registrar_bitacora(self.request, 'Actualizó un tipo de pago', modulo='Pagos', objeto_afectado=tipo.nombre)

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, 'Eliminó un tipo de pago', modulo='Pagos', objeto_afectado=instance.nombre)
        instance.delete()

class CarritoViewSet(viewsets.ModelViewSet):
    serializer_class = CarritoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Carrito.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        carrito = serializer.save()
        registrar_bitacora(self.request, 'Creó un carrito', modulo='Carrito', referencia_id=str(carrito.id))

    def perform_update(self, serializer):
        carrito = serializer.save()
        registrar_bitacora(self.request, 'Actualizó un carrito', modulo='Carrito', referencia_id=str(carrito.id))

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, 'Eliminó un carrito', modulo='Carrito', referencia_id=str(instance.id))
        instance.delete()


    @action(detail=False, methods=['get'], url_path='activo')
    def obtener_carrito_activo(self, request):
        carrito = Carrito.objects.filter(usuario=request.user, estado='activo').first()
        if carrito:
            serializer = self.get_serializer(carrito)
            return Response(serializer.data)
        return Response({'detalle': 'No hay carrito activo'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='total-items')
    def contar_items_carrito(self, request):
        user = request.user
        carrito = Carrito.objects.filter(usuario=user, estado='activo').first()
        if not carrito:
            return Response({'total_items': 0, 'total_cantidad': 0})

        total_items = carrito.items.count()
        total_cantidad = sum(item.cantidad for item in carrito.items.all())

        return Response({
            'total_items': total_items,  # número de productos distintos
            'total_cantidad': total_cantidad  # suma de todas las cantidades
        })

    @action(detail=False, methods=['get'], url_path='todos', permission_classes=[permissions.IsAuthenticated])
    def obtener_todos_los_carritos(self, request):
        carritos = Carrito.objects.prefetch_related('items__producto').select_related('usuario').all().order_by(
            '-fecha_actualizacion')
        serializer = CarritoConItemsSerializer(carritos, many=True)
        return Response(serializer.data)
class ItemCarritoViewSet(viewsets.ModelViewSet):
    serializer_class = ItemCarritoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ItemCarrito.objects.filter(carrito__usuario=user, carrito__estado='activo')

    def perform_create(self, serializer):
        item = serializer.save()
        registrar_bitacora(
            self.request,
            'Agregó un producto al carrito',
            modulo='Carrito',
            referencia_id=str(item.carrito.id)
        )

    def perform_update(self, serializer):
        item = serializer.save()
        registrar_bitacora(
            self.request,
            'Actualizó un ítem del carrito',
            modulo='Carrito',
            referencia_id=str(item.carrito.id)
        )

    def perform_destroy(self, instance):
        carrito = instance.carrito
        precio_unitario = instance.producto.get_precio_con_descuento()
        cantidad = instance.cantidad

        # ✅ Restar el total del ítem al carrito
        carrito.total_estimado -= Decimal(str(precio_unitario)) * cantidad

        # ✅ Eliminar el ítem
        instance.delete()

        # ✅ Si el carrito queda vacío, total en 0
        if not carrito.items.exists():
            carrito.total_estimado = 0

        carrito.save()

        # ✅ Registrar bitácora
        registrar_bitacora(
            self.request,
            'Eliminó un ítem del carrito',
            modulo='Carrito',
            referencia_id=str(carrito.id)
        )

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Venta
from .serializers import VentaSerializer
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils.timezone import make_aware

class VentaViewSet(viewsets.ModelViewSet):
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        queryset = Venta.objects.filter(usuario=user).order_by('-fecha_venta')

        filtro = self.request.query_params.get('filtro')
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')

        hoy = datetime.now()
        if filtro == 'hoy':
            inicio = make_aware(hoy.replace(hour=0, minute=0, second=0))
            fin = make_aware(hoy.replace(hour=23, minute=59, second=59))
            queryset = queryset.filter(fecha_venta__range=(inicio, fin))

        elif filtro == 'ayer':
            ayer = hoy - timedelta(days=1)
            inicio = make_aware(ayer.replace(hour=0, minute=0, second=0))
            fin = make_aware(ayer.replace(hour=23, minute=59, second=59))
            queryset = queryset.filter(fecha_venta__range=(inicio, fin))

        elif filtro == 'mes':
            inicio_mes = hoy.replace(day=1)
            fin_mes = (inicio_mes + relativedelta(months=1)) - timedelta(seconds=1)
            queryset = queryset.filter(
                fecha_venta__range=(make_aware(inicio_mes), make_aware(fin_mes))
            )

        elif desde and hasta:
            try:
                desde_date = make_aware(datetime.strptime(desde, "%Y-%m-%d"))
                hasta_date = make_aware(datetime.strptime(hasta, "%Y-%m-%d"))
                queryset = queryset.filter(fecha_venta__range=(desde_date, hasta_date))
            except ValueError:
                pass  # formato incorrecto, ignorar el filtro

        return queryset

    def perform_create(self, serializer):
        venta = serializer.save()
        registrar_bitacora(self.request, 'Confirmó una venta', modulo='Ventas', referencia_id=str(venta.id))

    def perform_update(self, serializer):
        venta = serializer.save()
        registrar_bitacora(self.request, 'Actualizó una venta', modulo='Ventas', referencia_id=str(venta.id))

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, 'Eliminó una venta', modulo='Ventas', referencia_id=str(instance.id))
        instance.delete()

    @action(detail=False, methods=['get'], url_path='todas')
    def todas_las_ventas(self, request):
        """
        Retorna todas las ventas con sus detalles, sin restricciones de usuario.
        """
        ventas = Venta.objects.all() \
            .select_related('usuario', 'tipo_pago') \
            .prefetch_related('detalles__producto') \
            .order_by('-fecha_venta')

        serializer = self.get_serializer(ventas, many=True)
        return Response(serializer.data)
from rest_framework import viewsets
from ventas.models import CampañaDescuento, Descuento
from ventas.serializers import CampañaDescuentoSerializer, DescuentoSerializer
from rest_framework.permissions import IsAuthenticated
from ventas.utils.notificaciones import enviar_notificacion_campaña_activa

class CampañaDescuentoViewSet(viewsets.ModelViewSet):
    queryset = CampañaDescuento.objects.all().order_by('-fecha_inicio')
    serializer_class = CampañaDescuentoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        campaña = serializer.save()
        registrar_bitacora(
            self.request,
            accion='Creó una campaña de descuentos',
            modulo='Descuentos',
            objeto_afectado=campaña.nombre
        )

        # 🔔 Enviar notificación a todos los clientes
        enviar_notificacion_campaña_activa(campaña)

    def perform_update(self, serializer):
        campaña = serializer.save()
        registrar_bitacora(
            self.request,
            accion='Actualizó una campaña de descuentos',
            modulo='Descuentos',
            objeto_afectado=campaña.nombre
        )

    def perform_destroy(self, instance):
        registrar_bitacora(
            self.request,
            accion='Eliminó una campaña de descuentos',
            modulo='Descuentos',
            objeto_afectado=instance.nombre
        )
        instance.delete()



class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.select_related('producto', 'campaña').all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        descuento = serializer.save()
        registrar_bitacora(self.request, 'Creó un descuento', modulo='Descuentos', objeto_afectado=descuento.producto.nombre)

    def perform_update(self, serializer):
        descuento = serializer.save()
        registrar_bitacora(self.request, 'Actualizó un descuento', modulo='Descuentos', objeto_afectado=descuento.producto.nombre)

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, 'Eliminó un descuento', modulo='Descuentos', objeto_afectado=instance.producto.nombre)
        instance.delete()

from rest_framework import viewsets, permissions
from ventas.models import Factura
from ventas.serializers import FacturaSerializer
from usuarios.utils.bitacora_utils import registrar_bitacora

class FacturaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Factura.objects.select_related('venta', 'venta__usuario').order_by('-fecha_emision')
    serializer_class = FacturaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        registrar_bitacora(request, 'Consultó la lista de facturas', modulo='Facturación')
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        factura = self.get_object()
        registrar_bitacora(request, f'Consultó la factura #{factura.numero_factura}', modulo='Facturación')
        return super().retrieve(request, *args, **kwargs)
