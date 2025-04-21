# views.py

from rest_framework import viewsets, status, permissions
from django.contrib.auth.models import Group, Permission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import date, timedelta
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from .models import Usuario, Bitacora
from .serializers import UsuarioSerializer, LoginSerializer, GroupSerializer, PermissionSerializer
from django.contrib.auth.models import Group
from utils.email_utils import generar_codigo_verificacion, enviar_codigo_verificacion
from .utils.bitacora_utils import registrar_bitacora
# views.py (agrega esta vista debajo de RegistroClienteManualView)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Usuario

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Usuario

class EliminarRegistroPendienteView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'El correo es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.get(email=email)

            if user.activo:
                return Response({'error': 'Este usuario ya está verificado, no se puede eliminar.'}, status=status.HTTP_400_BAD_REQUEST)

            user.delete()
            registrar_bitacora(
                request,
                accion='Eliminó su cuenta pendiente de verificación',
                modulo='Registro',
                detalle=f"Eliminación manual de cuenta con email: {email}",
                usuario=user
            )

            return Response({'message': 'Registro eliminado correctamente'}, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

class VerificarCodigoView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        codigo = request.data.get('codigo')

        if not email or not codigo:
            return Response({'error': 'Email y código son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.get(email=email)

            if user.activo:
                return Response({'message': 'Este usuario ya está verificado'}, status=status.HTTP_200_OK)

            if user.codigo_verificacion != codigo:
                return Response({'error': 'Código incorrecto'}, status=status.HTTP_400_BAD_REQUEST)

            if user.expiracion_codigo and timezone.now() > user.expiracion_codigo:
                return Response({'error': 'El código ha expirado'}, status=status.HTTP_400_BAD_REQUEST)

            user.activo = True
            user.codigo_verificacion = None
            user.expiracion_codigo = None
            user.save()
            registrar_bitacora(
                request,
                accion='Verificó su cuenta con código',
                modulo='Verificación',
                detalle=f"Verificación exitosa para el correo {user.email}",
                usuario=user
            )

            return Response({'message': 'Cuenta verificada exitosamente'}, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

class ReenviarCodigoView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'El correo es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.get(email=email)

            if user.activo:
                return Response({'message': 'Este usuario ya está verificado'}, status=status.HTTP_200_OK)

            nuevo_codigo = generar_codigo_verificacion()
            user.codigo_verificacion = nuevo_codigo
            user.expiracion_codigo = timezone.now() + timedelta(minutes=10)
            user.save()
            registrar_bitacora(
                request,
                accion='Solicitó nuevo código de verificación',
                modulo='Verificación',
                detalle=f"Reenvío solicitado para el correo {user.email}",
                usuario=user
            )

            enviado = enviar_codigo_verificacion(user.email, nuevo_codigo)
            if not enviado:
                return Response({'error': 'Error al reenviar el correo'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'message': 'Nuevo código enviado correctamente'}, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Usuario.objects.all()
        rol = self.request.query_params.get('rol')
        busqueda = self.request.query_params.get('busqueda')

        if rol:
            queryset = queryset.filter(groups__name=rol)

        if busqueda:
            queryset = queryset.filter(
                Q(first_name__icontains=busqueda) |
                Q(last_name__icontains=busqueda) |
                Q(ci__icontains=busqueda)
            )

        return queryset

    def perform_create(self, serializer):
        usuario = serializer.save()
        # Si tienes autenticación, puedes usar self.request.user
        registrar_bitacora(
            self.request,
            accion=f"Creó al usuario {usuario.username}",
            modulo='Usuarios',
            objeto_afectado='Usuario',
            referencia_id=str(usuario.id),
            detalle=f"Usuario creado: {usuario.email}"
        )

    def perform_update(self, serializer):
        usuario = serializer.save()
        registrar_bitacora(
            self.request,
            accion=f"Actualizó al usuario {usuario.username}",
            modulo='Usuarios',
            objeto_afectado='Usuario',
            referencia_id=str(usuario.id),
            detalle=f"Actualización del usuario: {usuario.email}"
        )

    def perform_destroy(self, instance):
        registrar_bitacora(
            self.request,
            accion=f"Eliminó al usuario {instance.username}",
            modulo='Usuarios',
            objeto_afectado='Usuario',
            referencia_id=str(instance.id),
            detalle=f"Usuario eliminado: {instance.email}"
        )
        instance.delete()


class RegistroClienteManualView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data

        if not all(key in data for key in ['username', 'password', 'email']):
            return Response({'error': 'Faltan campos obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica si el correo ya está registrado
        if Usuario.objects.filter(email=data['email']).exists():
            return Response({'error': 'El correo ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica si el username ya está registrado
        if Usuario.objects.filter(username=data['username']).exists():
            return Response({'error': 'El nombre de usuario ya está en uso'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                ci=data.get('ci', ''),
                celular=data.get('celular', ''),
                direccion=data.get('direccion', ''),
            )
            user.fecha_ingreso = date.today()
            user.activo = False

            if 'foto_perfil' in request.FILES:
                user.foto_perfil = request.FILES['foto_perfil']

            codigo = generar_codigo_verificacion()
            user.codigo_verificacion = codigo
            user.expiracion_codigo = timezone.now() + timedelta(minutes=10)
            user.save()

            grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
            user.groups.add(grupo_cliente)

            enviado = enviar_codigo_verificacion(user.email, codigo)
            if not enviado:
                return Response({'error': 'Error al enviar el correo de verificación'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            registrar_bitacora(
                request,
                accion='Registro manual del cliente',
                modulo='Registro',
                objeto_afectado='Usuario',
                referencia_id=str(user.id),
                detalle=f"Registro desde frontend con correo {user.email}",
                usuario=user
            )
            return Response({
                'message': 'Usuario registrado. Revisa tu correo para verificar tu cuenta.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'error': 'Contraseña incorrecta'}, status=status.HTTP_401_UNAUTHORIZED)

        # Bitácora

        refresh = RefreshToken.for_user(user)

        foto_url = user.foto_perfil.url if user.foto_perfil else None
        user_groups = user.groups.all()
        role = user_groups[0].name if user_groups else None

        user_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'email': user.email,
            'foto_perfil': foto_url,
            'role': role
        }
        registrar_bitacora(
            request,
            accion='Inicio de sesión',
            modulo='Autenticación',
            detalle='Inicio de sesión exitoso',
            objeto_afectado='Usuario',
            referencia_id=str(user.id),
            dispositivo='web',
            usuario_override=user  # ✅ este es el parámetro correcto
        )

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_data': user_data
        })

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    user = request.user
    registrar_bitacora(
        request,
        accion='Cierre de sesión',
        modulo='Autenticación',
        detalle='Logout desde frontend'
    )
    return Response({'message': 'Logout exitoso'})

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "No se permite eliminar roles."}, status=405)

    def perform_create(self, serializer):
        grupo = serializer.save()
        registrar_bitacora(
            self.request,
            accion=f"Creó el rol '{grupo.name}'",
            modulo='Roles',
            objeto_afectado='Group',
            referencia_id=str(grupo.id)
        )

    def perform_update(self, serializer):
        grupo = serializer.save()
        registrar_bitacora(
            self.request,
            accion=f"Actualizó el rol '{grupo.name}'",
            modulo='Roles',
            objeto_afectado='Group',
            referencia_id=str(grupo.id)
        )

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "No se permite eliminar roles."}, status=405)

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

class ActualizarFCMTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("fcm_token")
        if not token:
            return Response({'error': 'Token FCM requerido'}, status=400)

        user = request.user
        user.fcm_token = token
        user.save()
        registrar_bitacora(
            request,
            accion='Actualizó su token FCM',
            modulo='Notificaciones',
            detalle='Token FCM actualizado desde la app móvil o web'
        )

        return Response({'message': 'Token FCM actualizado correctamente'})
# views.py

from rest_framework import viewsets, permissions, filters
from .models import Bitacora
from .serializers import BitacoraSerializer

class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bitacora.objects.select_related('usuario').all()
    serializer_class = BitacoraSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['usuario__username', 'accion', 'detalles']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
