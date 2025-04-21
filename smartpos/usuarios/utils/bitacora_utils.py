from ..models import Bitacora

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def registrar_bitacora(
    request,
    accion,
    modulo=None,
    detalle=None,
    objeto_afectado=None,
    referencia_id=None,
    dispositivo="web",
    usuario_override=None  # ✅ Nuevo parámetro opcional
):
    usuario = usuario_override or request.user

    Bitacora.objects.create(
        usuario=usuario,
        accion=accion,
        modulo=modulo,
        detalle=detalle,
        objeto_afectado=objeto_afectado,
        referencia_id=referencia_id,
        ip_origen=get_client_ip(request),
        dispositivo=dispositivo
    )
