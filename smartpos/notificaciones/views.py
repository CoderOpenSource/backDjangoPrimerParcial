from rest_framework import generics, permissions
from notificaciones.models import Notificacion
from notificaciones.serializers import NotificacionSerializer
from notificaciones.pagination import NotificacionesPagination
from usuarios.utils.bitacora_utils import registrar_bitacora
from datetime import datetime, timedelta


class NotificacionesUsuarioView(generics.ListAPIView):
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificacionesPagination

    def get_queryset(self):
        user = self.request.user
        qs = Notificacion.objects.filter(usuario=user)

        filtro = self.request.query_params.get('filtro')
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')

        hoy = datetime.now().date()

        if filtro == 'hoy':
            qs = qs.filter(fecha_creacion__date=hoy)
        elif filtro == 'ayer':
            ayer = hoy - timedelta(days=1)
            qs = qs.filter(fecha_creacion__date=ayer)
        elif filtro == 'mes':
            qs = qs.filter(fecha_creacion__year=hoy.year, fecha_creacion__month=hoy.month)
        elif desde and hasta:
            try:
                desde_dt = datetime.strptime(desde, "%Y-%m-%d")
                hasta_dt = datetime.strptime(hasta, "%Y-%m-%d")
                qs = qs.filter(fecha_creacion__date__range=[desde_dt, hasta_dt])
            except ValueError:
                pass  # Puedes registrar un warning o ignorar

        qs = qs.order_by('-fecha_creacion')

        # Marcar como leídas las no leídas
        no_leidas = qs.filter(leido=False)
        cantidad = no_leidas.count()
        no_leidas.update(leido=True)

        registrar_bitacora(
            self.request,
            accion='Consultó sus notificaciones',
            modulo='Notificaciones',
            detalle=f"Consultó notificaciones. {cantidad} marcadas como leídas.",
            objeto_afectado='Notificacion',
            referencia_id=str(user.id)
        )

        return qs


class NotificacionesAdminView(generics.ListAPIView):
    queryset = Notificacion.objects.all().order_by('-fecha_creacion')
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]  # o tu permiso personalizado
    pagination_class = NotificacionesPagination

    def get_queryset(self):
        qs = self.queryset
        filtro = self.request.query_params.get('filtro')
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')

        hoy = datetime.now().date()

        if filtro == 'hoy':
            qs = qs.filter(fecha_creacion__date=hoy)
        elif filtro == 'ayer':
            ayer = hoy - timedelta(days=1)
            qs = qs.filter(fecha_creacion__date=ayer)
        elif filtro == 'mes':
            qs = qs.filter(fecha_creacion__year=hoy.year, fecha_creacion__month=hoy.month)
        elif desde and hasta:
            try:
                desde_dt = datetime.strptime(desde, "%Y-%m-%d")
                hasta_dt = datetime.strptime(hasta, "%Y-%m-%d")
                qs = qs.filter(fecha_creacion__date__range=[desde_dt, hasta_dt])
            except ValueError:
                pass

        return qs

    def get(self, request, *args, **kwargs):
        registrar_bitacora(
            request,
            accion='Consultó todas las notificaciones del sistema',
            modulo='Notificaciones',
            detalle='Vista administrativa de todas las notificaciones.',
            objeto_afectado='Notificacion'
        )
        return super().get(request, *args, **kwargs)
