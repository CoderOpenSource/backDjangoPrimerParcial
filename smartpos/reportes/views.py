from django.http import HttpResponse
from django.views import View
from django.utils import timezone
from ventas.models import Venta, DetalleVenta
from productos.models import Producto, MovimientoInventario
from .utils.pdf import generar_pdf_ventas_por_fecha, generar_pdf_productos_mas_vendidos, generar_pdf_inventario
from .utils.excel import generar_excel_ventas_por_fecha, generar_excel_inventario, generar_excel_productos_mas_vendidos
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
class VentasPorRangoFechaPDFView(View):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        usuario_id = request.GET.get('cliente')
        tipo_pago = request.GET.get('tipo_pago')
        estado = request.GET.get('estado')

        print(f"🧾 Parámetros recibidos:")
        print(f"  Fecha inicio: {fecha_inicio}")
        print(f"  Fecha fin: {fecha_fin}")
        print(f"  Usuario ID: {usuario_id}")
        print(f"  Tipo de pago: {tipo_pago}")
        print(f"  Estado: {estado}")

        filtros = {}
        columnas_extra = []

        # Convertir las fechas solo si están presentes
        fecha_inicio_dt = None
        fecha_fin_dt = None

        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")

        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(
                days=1)  # sumamos un día para incluir toda la fecha_fin

        # Aplicar filtros usando datetime
        if fecha_inicio_dt and fecha_fin_dt:
            filtros['fecha_venta__range'] = [fecha_inicio_dt, fecha_fin_dt]
        elif fecha_inicio_dt:
            filtros['fecha_venta__gte'] = fecha_inicio_dt
        elif fecha_fin_dt:
            filtros['fecha_venta__lt'] = fecha_fin_dt  # menor que porque ya sumamos un día

        if usuario_id and usuario_id.isdigit():
            filtros['usuario_id'] = int(usuario_id)
            columnas_extra.append('cliente')
            print(f"✔️ Filtrando por usuario_id: {usuario_id}")

        if tipo_pago:
            filtros['tipo_pago_id'] = tipo_pago
            columnas_extra.append('metodo_pago')

        if estado:
            filtros['estado'] = estado
            columnas_extra.append('estado')

        print(f"🔍 Filtros aplicados: {filtros}")

        ventas = Venta.objects.filter(**filtros).prefetch_related(
            'detalles__producto', 'usuario', 'tipo_pago'
        )

        pdf = generar_pdf_ventas_por_fecha(ventas, fecha_inicio, fecha_fin, columnas_extra, usuario_id)
        return HttpResponse(pdf, content_type='application/pdf')



class VentasPorRangoFechaExcelView(View):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        usuario_id = request.GET.get('cliente')
        tipo_pago = request.GET.get('tipo_pago')
        estado = request.GET.get('estado')

        print("📊 [EXCEL] Parámetros recibidos:")
        print(f"  Fecha inicio: {fecha_inicio}")
        print(f"  Fecha fin: {fecha_fin}")
        print(f"  Usuario ID: {usuario_id}")
        print(f"  Tipo de pago: {tipo_pago}")
        print(f"  Estado: {estado}")

        filtros = {}
        columnas_extra = []
        usuario = None

        # Convertir las fechas solo si están presentes
        fecha_inicio_dt = None
        fecha_fin_dt = None

        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")

        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(
                days=1)  # sumamos un día para incluir toda la fecha_fin

        # Aplicar filtros usando datetime
        if fecha_inicio_dt and fecha_fin_dt:
            filtros['fecha_venta__range'] = [fecha_inicio_dt, fecha_fin_dt]
        elif fecha_inicio_dt:
            filtros['fecha_venta__gte'] = fecha_inicio_dt
        elif fecha_fin_dt:
            filtros['fecha_venta__lt'] = fecha_fin_dt  # menor que porque ya sumamos un día

        if usuario_id and usuario_id.isdigit():
            filtros['usuario_id'] = int(usuario_id)
            columnas_extra.append('cliente')
            print(f"✔️ Filtrando por usuario_id: {usuario_id}")
            User = get_user_model()
            usuario = User.objects.filter(id=usuario_id).first()

        if tipo_pago:
            filtros['tipo_pago_id'] = tipo_pago
            columnas_extra.append('metodo_pago')

        if estado:
            filtros['estado'] = estado
            columnas_extra.append('estado')

        print(f"🔍 Filtros aplicados: {filtros}")

        ventas = Venta.objects.filter(**filtros).prefetch_related(
            'detalles__producto', 'usuario', 'tipo_pago'
        )

        excel = generar_excel_ventas_por_fecha(ventas, fecha_inicio, fecha_fin, columnas_extra, usuario)
        response = HttpResponse(excel, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="ventas_por_fecha.xlsx"'
        return response



from django.http import HttpResponse
from django.views import View
from django.db.models import Sum, Max
from datetime import datetime, timedelta
from productos.models import Producto, Stock, Categoria, Subcategoria, Marca
from ventas.models import DetalleVenta
from .utils.pdf import generar_pdf_productos_mas_vendidos


class ProductosMasVendidosPDFView(View):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        categoria_id = request.GET.get('categoria')
        subcategoria_id = request.GET.get('subcategoria')
        marca_id = request.GET.get('marca')

        filtros = {}

        # Fechas
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d") if fecha_inicio else None
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1) if fecha_fin else None

        if fecha_inicio_dt and fecha_fin_dt:
            filtros['venta__fecha_venta__range'] = [fecha_inicio_dt, fecha_fin_dt]
        elif fecha_inicio_dt:
            filtros['venta__fecha_venta__gte'] = fecha_inicio_dt
        elif fecha_fin_dt:
            filtros['venta__fecha_venta__lt'] = fecha_fin_dt

        if categoria_id:
            filtros['producto__subcategoria__categoria_id'] = categoria_id
        if subcategoria_id:
            filtros['producto__subcategoria_id'] = subcategoria_id
        if marca_id:
            filtros['producto__marca_id'] = marca_id

        print("📊 [PDF] Filtros aplicados:", filtros)

        # Obtener los top 10 productos más vendidos con fecha última venta
        top_productos = (
            DetalleVenta.objects.filter(**filtros)
            .values('producto_id')
            .annotate(
                total_vendido=Sum('cantidad'),
                ultima_venta=Max('venta__fecha_venta')
            )
            .order_by('-total_vendido')[:10]
        )

        producto_ids = [item['producto_id'] for item in top_productos]

        # Guardar cantidad + fecha por producto
        ventas_dict = {
            item['producto_id']: {
                'total': item['total_vendido'],
                'fecha': item['ultima_venta']
            }
            for item in top_productos
        }

        # Obtener productos con relaciones necesarias
        productos = Producto.objects.filter(id__in=producto_ids).select_related(
            'subcategoria__categoria', 'marca', 'stock'
        )

        # Reordenar los productos según ventas
        productos = sorted(productos, key=lambda p: ventas_dict.get(p.id, {}).get('total', 0), reverse=True)

        # Obtener nombres para los filtros
        categoria_nombre = Categoria.objects.filter(id=categoria_id).first().nombre if categoria_id else None
        subcategoria_nombre = Subcategoria.objects.filter(id=subcategoria_id).first().nombre if subcategoria_id else None
        marca_nombre = Marca.objects.filter(id=marca_id).first().nombre if marca_id else None

        # Generar PDF
        pdf = generar_pdf_productos_mas_vendidos(
            productos,
            ventas_dict,
            fecha_inicio,
            fecha_fin,
            categoria_nombre,
            subcategoria_nombre,
            marca_nombre
        )
        return HttpResponse(pdf, content_type='application/pdf')


from django.views import View
from django.http import HttpResponse
from django.db.models import Sum, Max
from datetime import datetime, timedelta
from productos.models import Producto, Categoria, Subcategoria, Marca
from ventas.models import DetalleVenta
from .utils.excel import generar_excel_productos_mas_vendidos  # asegúrate de tener esta ruta correcta

class ProductosMasVendidosExcelView(View):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        categoria_id = request.GET.get('categoria')
        subcategoria_id = request.GET.get('subcategoria')
        marca_id = request.GET.get('marca')

        filtros = {}

        # Fechas
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d") if fecha_inicio else None
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1) if fecha_fin else None

        if fecha_inicio_dt and fecha_fin_dt:
            filtros['venta__fecha_venta__range'] = [fecha_inicio_dt, fecha_fin_dt]
        elif fecha_inicio_dt:
            filtros['venta__fecha_venta__gte'] = fecha_inicio_dt
        elif fecha_fin_dt:
            filtros['venta__fecha_venta__lt'] = fecha_fin_dt

        if categoria_id:
            filtros['producto__subcategoria__categoria_id'] = categoria_id
        if subcategoria_id:
            filtros['producto__subcategoria_id'] = subcategoria_id
        if marca_id:
            filtros['producto__marca_id'] = marca_id

        print("📊 [EXCEL] Filtros aplicados:", filtros)

        # Top 10 productos más vendidos
        top_productos = (
            DetalleVenta.objects.filter(**filtros)
            .values('producto_id')
            .annotate(
                total_vendido=Sum('cantidad'),
                ultima_venta=Max('venta__fecha_venta')
            )
            .order_by('-total_vendido')[:10]
        )

        producto_ids = [item['producto_id'] for item in top_productos]
        ventas_dict = {
            item['producto_id']: {
                'total': item['total_vendido'],
                'fecha': item['ultima_venta']
            }
            for item in top_productos
        }

        productos = Producto.objects.filter(id__in=producto_ids).select_related(
            'subcategoria__categoria', 'marca', 'stock'
        )
        productos = sorted(productos, key=lambda p: ventas_dict.get(p.id, {}).get('total', 0), reverse=True)

        categoria_nombre = Categoria.objects.filter(id=categoria_id).first().nombre if categoria_id else None
        subcategoria_nombre = Subcategoria.objects.filter(id=subcategoria_id).first().nombre if subcategoria_id else None
        marca_nombre = Marca.objects.filter(id=marca_id).first().nombre if marca_id else None

        # Generar Excel
        excel_file = generar_excel_productos_mas_vendidos(
            productos,
            ventas_dict,
            fecha_inicio,
            fecha_fin,
            categoria_nombre,
            subcategoria_nombre,
            marca_nombre
        )

        response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="productos_mas_vendidos.xlsx"'
        return response


from django.http import HttpResponse
from django.views import View
from django.db.models import Q
from datetime import datetime, timedelta
from productos.models import MovimientoInventario, Producto, Categoria, Subcategoria
from .utils.pdf import generar_pdf_inventario


class ReporteInventarioPDFView(View):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        categoria_id = request.GET.get('categoria')
        subcategoria_id = request.GET.get('subcategoria')
        producto_id = request.GET.get('producto')
        tipo_movimiento = request.GET.get('tipo')  # entrada o salida

        filtros = Q()

        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            filtros &= Q(fecha_movimiento__gte=fecha_inicio_dt)
        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
            filtros &= Q(fecha_movimiento__lt=fecha_fin_dt)
        if categoria_id:
            filtros &= Q(producto__subcategoria__categoria_id=categoria_id)
        if subcategoria_id:
            filtros &= Q(producto__subcategoria_id=subcategoria_id)
        if producto_id:
            filtros &= Q(producto_id=producto_id)
        if tipo_movimiento in ['entrada', 'salida']:
            filtros &= Q(tipo=tipo_movimiento)

        print("📦 [PDF INVENTARIO] Filtros aplicados:", filtros)

        movimientos = MovimientoInventario.objects.filter(filtros).select_related(
            'producto__subcategoria__categoria', 'producto__marca'
        ).order_by('-fecha_movimiento')

        pdf = generar_pdf_inventario(
            movimientos,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria_id=categoria_id,
            subcategoria_id=subcategoria_id,
            producto_id=producto_id,
            tipo=tipo_movimiento
        )
        return HttpResponse(pdf, content_type='application/pdf')


from django.views import View
from django.http import HttpResponse
from django.db.models import Q
from datetime import datetime, timedelta
from productos.models import MovimientoInventario, Categoria, Subcategoria, Producto
from .utils.excel import generar_excel_inventario

class ReporteInventarioExcelView(View):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        categoria_id = request.GET.get('categoria')
        subcategoria_id = request.GET.get('subcategoria')
        producto_id = request.GET.get('producto')
        tipo_movimiento = request.GET.get('tipo')  # 'entrada' o 'salida'

        filtros = Q()

        # Fechas
        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            filtros &= Q(fecha_movimiento__gte=fecha_inicio_dt)

        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
            filtros &= Q(fecha_movimiento__lt=fecha_fin_dt)

        if categoria_id:
            filtros &= Q(producto__subcategoria__categoria_id=categoria_id)

        if subcategoria_id:
            filtros &= Q(producto__subcategoria_id=subcategoria_id)

        if producto_id:
            filtros &= Q(producto_id=producto_id)

        if tipo_movimiento:
            filtros &= Q(tipo=tipo_movimiento)

        print("📦 [EXCEL INVENTARIO] Filtros aplicados:", filtros)

        movimientos = MovimientoInventario.objects.filter(filtros).select_related(
            'producto__subcategoria__categoria', 'producto__stock'
        ).order_by('-fecha_movimiento')

        excel_file = generar_excel_inventario(movimientos)

        response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_inventario.xlsx"'
        return response
