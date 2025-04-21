from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    UsuarioViewSet,
    logout_view,
    GroupViewSet,
    PermissionViewSet,
    RegistroClienteManualView,
    VerificarCodigoView,
    ReenviarCodigoView,
    EliminarRegistroPendienteView,
ActualizarFCMTokenView,
BitacoraViewSet
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
router.register(r'roles', GroupViewSet, basename='roles')
router.register('permisos', PermissionViewSet)
router.register(r'bitacora', BitacoraViewSet, basename='bitacora')

urlpatterns = [
    # Endpoint personalizado ANTES del router para evitar conflictos
    path('registro/cliente/', RegistroClienteManualView.as_view(), name='registro-cliente'),

    path('verificar-codigo/', VerificarCodigoView.as_view(), name='verificar-codigo'),
    path('reenviar-codigo/', ReenviarCodigoView.as_view(), name='reenviar-codigo'),
    path('eliminar-registro/', EliminarRegistroPendienteView.as_view(), name='eliminar-registro'),
# urls.py
path('actualizar-fcm/', ActualizarFCMTokenView.as_view(), name='actualizar-fcm'),

    # Otros endpoints
    *router.urls,
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
