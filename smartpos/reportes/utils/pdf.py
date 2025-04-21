from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from django.contrib.auth import get_user_model

def generar_pdf_ventas_por_fecha(ventas, fecha_inicio=None, fecha_fin=None, columnas_extra=None, usuario_id=None):
    columnas_extra = columnas_extra or []
    User = get_user_model()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=80, bottomMargin=50, leftMargin=40, rightMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Label', fontName='Helvetica-Bold', textColor=colors.purple))
    styles.add(ParagraphStyle(name='SmallGray', fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Heading', fontName='Helvetica-Bold', fontSize=12, textColor=colors.black))

    elements = []

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(40, 750, "SMARTCART - Reporte de Ventas")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(550, 750, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(300, 30, "SmartCart - Sistema de Ventas Inteligente © 2025")
        canvas.drawRightString(550, 30, f"Página {doc.page}")
        canvas.restoreState()

    # Rango de fechas
    rango = "todas las ventas"
    if fecha_inicio and fecha_fin:
        rango = f"del {fecha_inicio} al {fecha_fin}"
    elif fecha_inicio:
        rango = f"desde el {fecha_inicio}"
    elif fecha_fin:
        rango = f"hasta el {fecha_fin}"

    cliente_nombre = None
    if columnas_extra and 'cliente' in columnas_extra:
        try:
            print("prueba")
            usuario = User.objects.get(id=usuario_id)
            cliente_nombre = f"{usuario.first_name} {usuario.last_name}"
            print(f"✅ Cliente encontrado: {cliente_nombre}")
        except Exception:
            cliente_nombre = None

    info_rango_cliente = f"<b>Rango de fechas:</b> {rango} &nbsp;&nbsp;&nbsp;&nbsp; <b>Cliente:</b> {cliente_nombre or 'Todos los clientes'}"
    elements.append(Paragraph(info_rango_cliente, styles['Normal']))
    elements.append(Spacer(1, 12))

    if not ventas.exists():
        elements.append(Paragraph("⚠️ <b>No se encontraron ventas con los filtros aplicados.</b>", styles['Heading']))
        elements.append(Spacer(1, 12))
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')

    for venta in ventas:
        cliente = venta.usuario if hasattr(venta, 'usuario') else None
        nombre = f"{cliente.first_name} {cliente.last_name}" if cliente else '---'
        metodo = venta.tipo_pago.nombre if venta.tipo_pago else '---'
        estado = venta.estado if hasattr(venta, 'estado') else '---'
        fecha = venta.fecha_venta.strftime('%d/%m/%Y %H:%M') if hasattr(venta, 'fecha_venta') and venta.fecha_venta else '---'
        ci = cliente.ci if cliente and hasattr(cliente, 'ci') else '---'
        celular = cliente.celular if cliente and hasattr(cliente, 'celular') else '---'
        direccion = cliente.direccion if cliente and hasattr(cliente, 'direccion') else '---'

        # Ficha dividida en dos columnas por fila
        resumen_data = [
            ['Venta ID', f'{venta.id}', 'Cliente', nombre],
            ['CI Cliente', ci, 'Celular', celular],
            ['Dirección', direccion, 'Pago', metodo],
            ['Estado', estado, 'Fecha', fecha],
            ['Total', f'{venta.total:.2f} Bs', '', '']
        ]

        resumen_table = Table(resumen_data, colWidths=[80, 170, 80, 170])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('BACKGROUND', (0, 0), (0, -1), colors.purple),  # Columna izquierda
             ('BACKGROUND', (2, 0), (2, -1), colors.purple),  # Columna derecha de atributos
      # Tercera columna fondo púrpura
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        elements.append(resumen_table)
        elements.append(Spacer(1, 10))

        # Título
        elements.append(Paragraph("Productos asociados a la venta:", styles['Heading']))
        elements.append(Spacer(1, 4))

        # Detalles de productos
        data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
        for detalle in venta.detalles.all():
            data.append([
                detalle.producto.nombre,
                detalle.cantidad,
                f"{detalle.precio_unitario:.2f} Bs",
                f"{detalle.precio_unitario * detalle.cantidad:.2f} Bs"
            ])
        data.append(['', '', Paragraph('<b>Total:</b>', styles['Normal']), f"{venta.total:.2f} Bs"])

        table = Table(data, colWidths=[200, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lavender),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 24))

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

from io import BytesIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.views import View
from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from ventas.models import DetalleVenta, Producto


from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.http import HttpResponse
from datetime import datetime
from django.contrib.auth import get_user_model
from collections import Counter

def generar_pdf_ventas_por_fecha(ventas, fecha_inicio=None, fecha_fin=None, columnas_extra=None, usuario_id=None):
    columnas_extra = columnas_extra or []
    User = get_user_model()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=80, bottomMargin=50, leftMargin=40, rightMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Label', fontName='Helvetica-Bold', textColor=colors.purple))
    styles.add(ParagraphStyle(name='SmallGray', fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Heading', fontName='Helvetica-Bold', fontSize=12, textColor=colors.black))

    elements = []

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(40, 750, "SMARTCART - Reporte de Ventas")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(550, 750, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(300, 30, "SmartCart - Sistema de Ventas Inteligente © 2025")
        canvas.drawRightString(550, 30, f"Página {doc.page}")
        canvas.restoreState()

    rango = "todas las ventas"
    if fecha_inicio and fecha_fin:
        rango = f"del {fecha_inicio} al {fecha_fin}"
    elif fecha_inicio:
        rango = f"desde el {fecha_inicio}"
    elif fecha_fin:
        rango = f"hasta el {fecha_fin}"

    cliente_nombre = None
    if columnas_extra and 'cliente' in columnas_extra:
        try:
            usuario = User.objects.get(id=usuario_id)
            cliente_nombre = f"{usuario.first_name} {usuario.last_name}"
        except Exception:
            cliente_nombre = None

    info_rango_cliente = f"<b>Rango de fechas:</b> {rango} &nbsp;&nbsp;&nbsp;&nbsp; <b>Cliente:</b> {cliente_nombre or 'Todos los clientes'}"
    elements.append(Paragraph(info_rango_cliente, styles['Normal']))
    elements.append(Spacer(1, 12))

    if not ventas.exists():
        elements.append(Paragraph("⚠️ <b>No se encontraron ventas con los filtros aplicados.</b>", styles['Heading']))
        elements.append(Spacer(1, 12))
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')

    productos_counter = Counter()
    clientes_gasto = {}
    metodos_pago = Counter()
    total_general = 0

    for venta in ventas:
        cliente = venta.usuario if hasattr(venta, 'usuario') else None
        nombre = f"{cliente.first_name} {cliente.last_name}" if cliente else '---'
        metodo = venta.tipo_pago.nombre if venta.tipo_pago else '---'
        estado = venta.estado if hasattr(venta, 'estado') else '---'
        fecha = venta.fecha_venta.strftime('%d/%m/%Y %H:%M') if venta.fecha_venta else '---'
        ci = getattr(cliente, 'ci', '---')
        celular = getattr(cliente, 'celular', '---')
        direccion = getattr(cliente, 'direccion', '---')

        clientes_gasto[nombre] = clientes_gasto.get(nombre, 0) + float(venta.total)
        metodos_pago[metodo] += 1
        total_general += float(venta.total)

        resumen_data = [
            ['Venta ID', f'{venta.id}', 'Cliente', nombre],
            ['CI Cliente', ci, 'Celular', celular],
            ['Dirección', direccion, 'Pago', metodo],
            ['Estado', estado, 'Fecha', fecha],
            ['Total', f'{venta.total:.2f} Bs', '', '']
        ]

        resumen_table = Table(resumen_data, colWidths=[80, 170, 80, 170])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('BACKGROUND', (0, 0), (0, -1), colors.purple),
            ('BACKGROUND', (2, 0), (2, -1), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))

        elements.append(resumen_table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("Productos asociados a la venta:", styles['Heading']))
        elements.append(Spacer(1, 4))

        data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
        for detalle in venta.detalles.all():
            productos_counter[detalle.producto.nombre] += detalle.cantidad
            subtotal = detalle.precio_unitario * detalle.cantidad
            data.append([
                detalle.producto.nombre,
                detalle.cantidad,
                f"{detalle.precio_unitario:.2f} Bs",
                f"{subtotal:.2f} Bs"
            ])
        data.append(['', '', Paragraph('<b>Total:</b>', styles['Normal']), f"{venta.total:.2f} Bs"])

        table = Table(data, colWidths=[200, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lavender),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 24))

    # Resumen final
    elements.append(Paragraph("🧾 <b>Resumen General:</b>", styles['Heading']))
    elements.append(Spacer(1, 6))

    if productos_counter:
        mas_vendido = productos_counter.most_common(1)[0]
        elements.append(Paragraph(f"<b>🔝 Producto más vendido:</b> {mas_vendido[0]} ({mas_vendido[1]} unidades)", styles['Normal']))
    if clientes_gasto:
        mejor_cliente = max(clientes_gasto.items(), key=lambda x: x[1])
        elements.append(Paragraph(f"<b>👑 Cliente que más gastó:</b> {mejor_cliente[0]} ({mejor_cliente[1]:.2f} Bs)", styles['Normal']))

    elements.append(Paragraph(f"<b>📦 Total de productos vendidos:</b> {sum(productos_counter.values())}", styles['Normal']))
    elements.append(Paragraph(f"<b>💰 Monto total vendido:</b> {total_general:.2f} Bs", styles['Normal']))

    if metodos_pago:
        metodos = ", ".join(f"{k}: {v}" for k, v in metodos_pago.items())
        elements.append(Paragraph(f"<b>💳 Métodos de pago utilizados:</b> {metodos}", styles['Normal']))

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


from collections import defaultdict

def generar_pdf_productos_mas_vendidos(productos, ventas_dict, fecha_inicio=None, fecha_fin=None, categoria_nombre=None,
                                       subcategoria_nombre=None, marca_nombre=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=80, bottomMargin=50, leftMargin=40, rightMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Label', fontName='Helvetica-Bold', textColor=colors.purple))
    styles.add(ParagraphStyle(name='SmallGray', fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Heading', fontName='Helvetica-Bold', fontSize=12, textColor=colors.black))

    elements = []

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(40, 750, "SMARTCART - Productos Más Vendidos")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(550, 750, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(300, 30, "SmartCart - Sistema de Ventas Inteligente © 2025")
        canvas.drawRightString(550, 30, f"Página {doc.page}")
        canvas.restoreState()

    # Rango de fechas
    rango = "todas las fechas"
    if fecha_inicio and fecha_fin:
        rango = f"del {fecha_inicio} al {fecha_fin}"
    elif fecha_inicio:
        rango = f"desde el {fecha_inicio}"
    elif fecha_fin:
        rango = f"hasta el {fecha_fin}"

    cat = categoria_nombre or "Todas"
    subcat = subcategoria_nombre or "Todas"
    marca = marca_nombre or "Todas"

    filtro_texto = (
        f"<b>Rango de fechas:</b> {rango}<br/>"
        f"<b>Categoría:</b> {cat} &nbsp;&nbsp;&nbsp;&nbsp; "
        f"<b>Subcategoría:</b> {subcat} &nbsp;&nbsp;&nbsp;&nbsp; "
        f"<b>Marca:</b> {marca}"
    )
    elements.append(Paragraph(filtro_texto, styles['Normal']))
    elements.append(Spacer(1, 12))

    if not productos:
        elements.append(Paragraph("⚠️ <b>No se encontraron productos para los filtros aplicados.</b>", styles['Heading']))
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
        buffer.seek(0)
        return buffer

    # Cabecera
    data = [['Producto', 'Categoría', 'Subcategoría', 'Marca',
             'Total', 'Ingreso', 'Ganancia', 'Última Venta']]

    total_ingreso = 0
    total_ganancia = 0
    fechas_venta = []
    ventas_por_categoria = defaultdict(int)
    producto_mas_vendido = ('---', 0)  # nombre, cantidad

    for producto in productos:
        venta = ventas_dict.get(producto.id, {})
        cantidad = venta.get('total', 0)
        fecha_venta = venta.get('fecha')

        ingreso = float(cantidad) * float(producto.precio_unitario)
        ganancia = float(cantidad) * (float(producto.precio_unitario) - float(producto.precio_compra or 0))

        total_ingreso += ingreso
        total_ganancia += ganancia

        if fecha_venta:
            fechas_venta.append(fecha_venta)

        categoria_nombre_actual = producto.subcategoria.categoria.nombre if producto.subcategoria and producto.subcategoria.categoria else '---'
        ventas_por_categoria[categoria_nombre_actual] += cantidad

        if cantidad > producto_mas_vendido[1]:
            producto_mas_vendido = (producto.nombre, cantidad)

        data.append([
            producto.nombre,
            categoria_nombre_actual,
            producto.subcategoria.nombre if producto.subcategoria else '---',
            producto.marca.nombre if producto.marca else '---',
            cantidad,
            f"{ingreso:.2f} Bs",
            f"{ganancia:.2f} Bs",
            fecha_venta.strftime('%d/%m/%Y %H:%M') if fecha_venta else '---'
        ])

    table = Table(data, colWidths=[90, 70, 70, 60, 50, 55, 80, 85])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    # Resumen
    if fecha_inicio and fecha_fin:
        resumen = f"<b>Total de ganancia generada en las fechas:</b> {fecha_inicio} al {fecha_fin}"
    elif fechas_venta:
        fechas_venta.sort()
        resumen = (
            f"<b>Total de ganancia generada desde:</b> {fechas_venta[0].strftime('%d/%m/%Y')} "
            f"<b>hasta</b> {fechas_venta[-1].strftime('%d/%m/%Y')}"
        )
    else:
        resumen = "<b>Total de ganancia generada:</b> sin fechas registradas"

    categoria_top = max(ventas_por_categoria.items(), key=lambda x: x[1])[0] if ventas_por_categoria else '---'
    producto_top = producto_mas_vendido[0]

    elements.append(Paragraph(resumen, styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Total Ingreso:</b> {total_ingreso:.2f} Bs", styles['Normal']))
    elements.append(Paragraph(f"<b>Total Ganancia:</b> {total_ganancia:.2f} Bs", styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Categoría más vendida:</b> {categoria_top}", styles['Normal']))
    elements.append(Paragraph(f"<b>Producto más vendido:</b> {producto_top}", styles['Normal']))

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    buffer.seek(0)
    return buffer
def generar_pdf_inventario(movimientos, fecha_inicio=None, fecha_fin=None,
                           categoria_id=None, subcategoria_id=None,
                           producto_id=None, tipo=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=80, bottomMargin=50, leftMargin=40, rightMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Label', fontName='Helvetica-Bold', textColor=colors.purple))
    styles.add(ParagraphStyle(name='SmallGray', fontSize=9, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Heading', fontName='Helvetica-Bold', fontSize=12, textColor=colors.black))

    elements = []

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(40, 750, "SMARTCART - Reporte de Inventario")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(550, 750, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawCentredString(300, 30, "SmartCart - Sistema de Ventas Inteligente © 2025")
        canvas.drawRightString(550, 30, f"Página {doc.page}")
        canvas.restoreState()

    # Filtros visibles al inicio (como en productos más vendidos)
    rango = "todas las fechas"
    if fecha_inicio and fecha_fin:
        rango = f"del {fecha_inicio} al {fecha_fin}"
    elif fecha_inicio:
        rango = f"desde el {fecha_inicio}"
    elif fecha_fin:
        rango = f"hasta el {fecha_fin}"

    filtros_aplicados = [
        f"<b>Rango de fechas:</b> {rango}",
        f"<b>Categoría ID:</b> {categoria_id or 'Todas'}",
        f"<b>Subcategoría ID:</b> {subcategoria_id or 'Todas'}",
        f"<b>Producto ID:</b> {producto_id or 'Todos'}",
        f"<b>Tipo Movimiento:</b> {tipo.capitalize() if tipo else 'Todos'}"
    ]

    elements.append(Paragraph("<br/>".join(filtros_aplicados), styles['Normal']))
    elements.append(Spacer(1, 12))

    if not movimientos:
        elements.append(Paragraph("⚠️ <b>No se encontraron movimientos para los filtros aplicados.</b>", styles['Heading']))
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
        buffer.seek(0)
        return buffer

    # Cabecera de la tabla
    data = [[
        'Producto', 'Categoría', 'Subcategoría', 'Marca',
        'Tipo', 'Cantidad', 'Fecha', 'Descripción']
    ]

    totales = {'entrada': 0, 'salida': 0}
    productos_afectados = set()
    fechas = []
    conteo_por_categoria = defaultdict(int)

    for m in movimientos:
        producto = m.producto
        productos_afectados.add(producto.id)
        cat = producto.subcategoria.categoria.nombre if producto.subcategoria and producto.subcategoria.categoria else '---'
        subcat = producto.subcategoria.nombre if producto.subcategoria else '---'
        marca = producto.marca.nombre if producto.marca else '---'
        fecha = m.fecha_movimiento.strftime('%d/%m/%Y %H:%M') if m.fecha_movimiento else '---'

        data.append([
            producto.nombre,
            cat,
            subcat,
            marca,
            m.tipo.capitalize(),
            m.cantidad,
            fecha,
            m.descripcion or '---'
        ])

        totales[m.tipo] += m.cantidad
        conteo_por_categoria[cat] += m.cantidad
        fechas.append(m.fecha_movimiento)

    table = Table(data, colWidths=[90, 70, 70, 60, 55, 50, 80, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    fechas.sort()
    resumen = (
        f"<b>Resumen de movimientos desde:</b> {fechas[0].strftime('%d/%m/%Y')} "
        f"<b>hasta</b> {fechas[-1].strftime('%d/%m/%Y')}"
    ) if fechas else "<b>Resumen de movimientos:</b> sin fechas registradas"

    categoria_top = max(conteo_por_categoria.items(), key=lambda x: x[1])[0] if conteo_por_categoria else '---'

    elements.append(Paragraph(resumen, styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Total de productos distintos con movimientos:</b> {len(productos_afectados)}", styles['Normal']))
    elements.append(Paragraph(f"<b>Total Entradas:</b> {totales['entrada']} unidades", styles['Normal']))
    elements.append(Paragraph(f"<b>Total Salidas:</b> {totales['salida']} unidades", styles['Normal']))
    elements.append(Paragraph(f"<b>Categoría con más movimientos:</b> {categoria_top}", styles['Normal']))

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    buffer.seek(0)
    return buffer
