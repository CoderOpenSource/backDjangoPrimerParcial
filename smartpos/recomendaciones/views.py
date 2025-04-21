
# 📁 recomendaciones/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from recomendaciones.utils.asociacion import obtener_sugerencias_desde_apriori
from productos.models import Producto
from productos.serializers import ProductoSerializer

class RecomendacionAprioriAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        productos_param = request.query_params.get('productos')
        if not productos_param:
            return Response({"error": "Debes proporcionar al menos un producto"}, status=400)

        productos_lista = [nombre.strip() for nombre in productos_param.split(',') if nombre.strip()]
        if not productos_lista:
            return Response({"error": "Lista vacía"}, status=400)

        nombres_sugeridos = obtener_sugerencias_desde_apriori(productos_lista)

        productos = Producto.objects.filter(nombre__in=nombres_sugeridos, estado=True)
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

# 📁 recomendaciones/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from recomendaciones.utils.historial import obtener_recomendaciones_por_historial
from productos.serializers import ProductoSerializer  # usa el tuyo

class RecomendacionesHistorialAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        recomendaciones = obtener_recomendaciones_por_historial(usuario)
        serializer = ProductoSerializer(recomendaciones, many=True, context={'request': request})
        return Response(serializer.data)
