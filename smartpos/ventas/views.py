# tipos_pago/views.py
from rest_framework import viewsets, permissions
from .models import TipoPago
from .serializers import TipoPagoSerializer

class TipoPagoViewSet(viewsets.ModelViewSet):
    queryset = TipoPago.objects.all()
    serializer_class = TipoPagoSerializer
    permission_classes = [permissions.IsAuthenticated]

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Carrito
from .serializers import CarritoSerializer

class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer
    permission_classes = [IsAuthenticated]
