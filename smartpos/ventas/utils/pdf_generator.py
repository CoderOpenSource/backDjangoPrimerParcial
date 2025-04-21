from django.template.loader import render_to_string
from xhtml2pdf import pisa
import tempfile
import cloudinary.uploader
import os


def generar_y_subir_pdf(venta, factura):
    try:
        # Renderizar HTML desde la plantilla ubicada en templates/ventas/factura_template.html
        html_string = render_to_string("ventas/factura_template.html", {
            "venta": venta,
            "factura": factura
        })

        # Crear archivo PDF temporal
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            pisa_status = pisa.CreatePDF(html_string, dest=tmp_pdf)
            tmp_pdf_path = tmp_pdf.name

        if pisa_status.err:
            raise Exception("❌ Error al generar el PDF con xhtml2pdf.")

        # Subir a Cloudinary como archivo RAW
        result = cloudinary.uploader.upload(
            tmp_pdf_path,
            resource_type="raw",
            folder="facturas",
            public_id=f"factura_{factura.numero_factura}"
        )

        return result['secure_url']

    finally:
        # Eliminar el archivo temporal después de subir (si existe)
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)
