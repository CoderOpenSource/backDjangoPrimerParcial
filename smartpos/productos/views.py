from rest_framework import viewsets
from .models import Categoria, Subcategoria, Producto, Stock, MovimientoInventario, ProductoFavorito, Marca
from .serializers import CategoriaSerializer, SubcategoriaSerializer, ProductoSerializer, StockSerializer, MovimientoInventarioSerializer, ProductoFavoritoSerializer, MarcaSerializer
from rest_framework.permissions import IsAuthenticated
from .pagination import ProductoPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
# arriba del archivo
from recomendaciones.utils.similares import obtener_productos_similares
from usuarios.utils.bitacora_utils import registrar_bitacora
from django.db.models import Sum
class ProductoViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoSerializer
    pagination_class = ProductoPagination
    permissions_classes = (IsAuthenticated)

    def perform_create(self, serializer):
        producto = serializer.save()
        registrar_bitacora(self.request, f"Creó el producto '{producto.nombre}'", modulo="Productos",
                           objeto_afectado=producto.nombre, referencia_id=str(producto.id))

    def perform_update(self, serializer):
        producto = serializer.save()
        registrar_bitacora(self.request, f"Actualizó el producto '{producto.nombre}'", modulo="Productos",
                           objeto_afectado=producto.nombre, referencia_id=str(producto.id))

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, f"Eliminó el producto '{instance.nombre}'", modulo="Productos",
                           objeto_afectado=instance.nombre, referencia_id=str(instance.id))
        instance.delete()

    def get_queryset(self):
        queryset = Producto.objects.all().select_related('stock') \
            .prefetch_related('imagenes', 'subcategoria__categoria')

        sin_stock = self.request.query_params.get('sin_stock')

        if self.action in ['list']:
            if sin_stock is None:
                # Si no se pasa nada, por defecto productos con stock
                queryset = queryset.filter(stock__cantidad_actual__gt=0)
            elif sin_stock == '1':
                # Solo productos SIN stock asociado (para registrar stock inicial)
                queryset = queryset.filter(stock__isnull=True)
            elif sin_stock == '0':
                queryset = queryset.filter(stock__cantidad_actual__gt=0)
            elif sin_stock == 'all':
                pass  # mostrar todos

        # Filtros adicionales
        subcategoria_id = self.request.query_params.get('subcategoria')
        categoria_id = self.request.query_params.get('categoria')
        mas_vendidos = self.request.query_params.get('mas_vendidos')
        nuevo = self.request.query_params.get('nuevo')
        oferta = self.request.query_params.get('oferta')

        if subcategoria_id:
            queryset = queryset.filter(subcategoria_id=subcategoria_id)
        elif categoria_id:
            queryset = queryset.filter(subcategoria__categoria_id=categoria_id)

        if mas_vendidos:
            queryset = Producto.objects.annotate(
                total_vendidos=Sum('detalles_venta__cantidad')
            ).filter(
                total_vendidos__gt=0  # solo productos que se vendieron al menos una vez
            ).order_by('-total_vendidos')[:10]

        if nuevo:
            hace_15_dias = timezone.now() - timedelta(days=15)
            queryset = queryset.filter(creado_en__gte=hace_15_dias).order_by('-creado_en')

        if oferta:
            ahora = timezone.now()
            queryset = queryset.filter(
                descuentos__activo=True,
                descuentos__campaña__activa=True,
                descuentos__campaña__fecha_inicio__lte=ahora,
                descuentos__campaña__fecha_fin__gte=ahora
            ).distinct()

        return queryset
    @action(detail=True, methods=["get"], url_path="similares")
    def similares(self, request, pk=None):
        try:
            producto = self.get_object()
            similares = obtener_productos_similares(producto)
            serializer = ProductoSerializer(similares, many=True, context={"request": request})
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def perform_create(self, serializer):
        cat = serializer.save()
        registrar_bitacora(self.request, f"Creó la categoría '{cat.nombre}'", modulo="Categorías",
                           objeto_afectado=cat.nombre)

    def perform_update(self, serializer):
        cat = serializer.save()
        registrar_bitacora(self.request, f"Actualizó la categoría '{cat.nombre}'", modulo="Categorías",
                           objeto_afectado=cat.nombre)

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, f"Eliminó la categoría '{instance.nombre}'", modulo="Categorías",
                           objeto_afectado=instance.nombre)
        instance.delete()


class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.all()
    serializer_class = SubcategoriaSerializer

    def perform_create(self, serializer):
        subcat = serializer.save()
        registrar_bitacora(self.request, f"Creó la subcategoría '{subcat.nombre}'", modulo="Subcategorías",
                           objeto_afectado=subcat.nombre, referencia_id=str(subcat.id))

    def perform_update(self, serializer):
        subcat = serializer.save()
        registrar_bitacora(self.request, f"Actualizó la subcategoría '{subcat.nombre}'", modulo="Subcategorías",
                           objeto_afectado=subcat.nombre, referencia_id=str(subcat.id))

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, f"Eliminó la subcategoría '{instance.nombre}'", modulo="Subcategorías",
                           objeto_afectado=instance.nombre, referencia_id=str(instance.id))
        instance.delete()


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related('producto').all()
    serializer_class = StockSerializer

    def perform_create(self, serializer):
        stock = serializer.save()
        registrar_bitacora(self.request, f"Registró stock inicial para '{stock.producto.nombre}'", modulo="Stock",
                           objeto_afectado=stock.producto.nombre, referencia_id=str(stock.producto.id))

    def perform_update(self, serializer):
        stock = serializer.save()
        registrar_bitacora(self.request, f"Actualizó el stock para '{stock.producto.nombre}'", modulo="Stock",
                           objeto_afectado=stock.producto.nombre, referencia_id=str(stock.producto.id))

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, f"Eliminó el stock de '{instance.producto.nombre}'", modulo="Stock",
                           objeto_afectado=instance.producto.nombre, referencia_id=str(instance.producto.id))
        instance.delete()


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all().order_by('-fecha_movimiento')
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        movimiento = serializer.save()
        registrar_bitacora(self.request, f"Registró un movimiento de inventario '{movimiento.tipo}'", modulo="Movimientos",
                           objeto_afectado=movimiento.producto.nombre, referencia_id=str(movimiento.producto.id),
                           detalle=f"{movimiento.cantidad} unidades - {movimiento.descripcion}")


class ProductoFavoritoViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoFavoritoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductoFavorito.objects.filter(usuario=self.request.user)

class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all().order_by('-creado_en')
    serializer_class = MarcaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        marca = serializer.save()
        registrar_bitacora(self.request, f"Creó la marca '{marca.nombre}'", modulo="Marcas",
                           objeto_afectado=marca.nombre, referencia_id=str(marca.id))

    def perform_update(self, serializer):
        marca = serializer.save()
        registrar_bitacora(self.request, f"Actualizó la marca '{marca.nombre}'", modulo="Marcas",
                           objeto_afectado=marca.nombre, referencia_id=str(marca.id))

    def perform_destroy(self, instance):
        registrar_bitacora(self.request, f"Eliminó la marca '{instance.nombre}'", modulo="Marcas",
                           objeto_afectado=instance.nombre, referencia_id=str(instance.id))
        instance.delete()



