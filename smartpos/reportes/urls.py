from django.urls import path
from .views import (
    VentasPorRangoFechaPDFView,
    VentasPorRangoFechaExcelView,
    ProductosMasVendidosPDFView,
    ProductosMasVendidosExcelView,
    ReporteInventarioPDFView,
    ReporteInventarioExcelView
)

urlpatterns = [
    # Ventas por fecha
    path('ventas-por-fecha/pdf/', VentasPorRangoFechaPDFView.as_view(), name='ventas_por_fecha_pdf'),
    path('ventas-por-fecha/excel/', VentasPorRangoFechaExcelView.as_view(), name='ventas_por_fecha_excel'),

    # Productos más vendidos
    path('productos-mas-vendidos/pdf/', ProductosMasVendidosPDFView.as_view(), name='productos_mas_vendidos_pdf'),
    path('productos-mas-vendidos/excel/', ProductosMasVendidosExcelView.as_view(), name='productos_mas_vendidos_excel'),

    # Inventario actual
    path('inventario/pdf/', ReporteInventarioPDFView.as_view(), name='inventario_pdf'),
    path('inventario/excel/', ReporteInventarioExcelView.as_view(), name='inventario_excel'),
]
