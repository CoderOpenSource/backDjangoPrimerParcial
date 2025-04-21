# 📁 recomendaciones/urls.py
from django.urls import path
from .views import RecomendacionAprioriAPIView, RecomendacionesHistorialAPIView

urlpatterns = [
    path('apriori/', RecomendacionAprioriAPIView.as_view(), name='recomendacion-apriori'),
    path('historial/', RecomendacionesHistorialAPIView.as_view(), name='recomendacion-historial'),  # 👈 Añadido
]
