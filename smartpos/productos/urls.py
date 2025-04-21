# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoriaViewSet, SubcategoriaViewSet, ProductoViewSet, StockViewSet, MovimientoInventarioViewSet, ProductoFavoritoViewSet, MarcaViewSet

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'subcategorias', SubcategoriaViewSet, basename='subcategoria')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'stock', StockViewSet, basename='stock')
router.register(r'movimientos', MovimientoInventarioViewSet, basename='movimientos')
router.register(r'favoritos', ProductoFavoritoViewSet, basename='favorito')
router.register(r'marcas', MarcaViewSet, basename='marcas')

urlpatterns = [
    path('', include(router.urls)),
]
