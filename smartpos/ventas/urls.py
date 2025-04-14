# tipos_pago/urls.py
from rest_framework.routers import DefaultRouter
from .views import TipoPagoViewSet, CarritoViewSet

router = DefaultRouter()
router.register(r'tipos-pago', TipoPagoViewSet, basename='tipopago')
router.register(r'carritos', CarritoViewSet, basename='carrito')
urlpatterns = router.urls
