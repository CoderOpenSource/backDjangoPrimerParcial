from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TipoPagoViewSet, CarritoViewSet, ItemCarritoViewSet, VentaViewSet, DescuentoViewSet, CampañaDescuentoViewSet, FacturaViewSet

router = DefaultRouter()
router.register(r'tipos-pago', TipoPagoViewSet, basename='tipopago')
router.register(r'carritos', CarritoViewSet, basename='carrito')
# urls.py
router.register(r'items-carrito', ItemCarritoViewSet, basename='itemcarrito')
router.register(r'ventas', VentaViewSet, basename='ventas')
router.register(r'campanas', CampañaDescuentoViewSet, basename='campanas')
router.register(r'descuentos', DescuentoViewSet, basename='descuentos')
router.register(r'facturas', FacturaViewSet, basename='facturas')
urlpatterns = [
    path('', include(router.urls)),
]
