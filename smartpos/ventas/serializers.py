# tipos_pago/serializers.py
from rest_framework import serializers
from .models import TipoPago, Carrito

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