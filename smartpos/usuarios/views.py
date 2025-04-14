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

from .models import Usuario, Bitacora
from .serializers import UsuarioSerializer, LoginSerializer, GroupSerializer, PermissionSerializer
from django.contrib.auth.models import Group
from utils.email_utils import generar_codigo_verificacion, enviar_codigo_verificacion

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

            enviado = enviar_codigo_verificacion(user.email, nuevo_codigo)
            if not enviado:
                return Response({'error': 'Error al reenviar el correo'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'message': 'Nuevo código enviado correctamente'}, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.AllowAny]

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
        Bitacora.objects.create(usuario=user, accion='Inicio de sesión', fecha=datetime.now())

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
    Bitacora.objects.create(usuario=user, accion='Cierre de sesión', fecha=datetime.now())
    return Response({'message': 'Logout exitoso'})

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "No se permite eliminar roles."}, status=405)

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
