from rest_framework import viewsets
from .models import Categoria, Subcategoria, Producto, Stock, MovimientoInventario
from .serializers import CategoriaSerializer, SubcategoriaSerializer, ProductoSerializer, StockSerializer, MovimientoInventarioSerializer
from rest_framework.permissions import IsAuthenticated

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('-id')
    serializer_class = ProductoSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.all()
    serializer_class = SubcategoriaSerializer

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related('producto').all()
    serializer_class = StockSerializer


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all().order_by('-fecha_movimiento')
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]

