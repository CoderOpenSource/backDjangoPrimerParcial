from rest_framework import serializers
from .models import Usuario
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all()
    )
    # ✅ Se permite lectura y escritura de imagen
    foto_perfil = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'ci', 'celular', 'direccion', 'fecha_ingreso', 'activo',
            'groups', 'password', 'foto_perfil'
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # ✅ Mostrar URL pública de Cloudinary si hay imagen
        rep['foto_perfil'] = instance.foto_perfil.build_url() if instance.foto_perfil else None
        return rep

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])

        # ✅ Valores por defecto
        validated_data.setdefault('activo', False)
        validated_data.setdefault('fecha_ingreso', timezone.now().date())

        usuario = Usuario(**validated_data)

        if password:
            usuario.set_password(password)
        usuario.save()

        if groups:
            usuario.groups.set(groups)

        return usuario

    def update(self, instance, validated_data):
        try:
            password = validated_data.pop('password', None)
            groups = validated_data.pop('groups', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if password:
                instance.set_password(password)

            instance.save()

            if groups is not None:
                instance.groups.set(groups)

            return instance
        except Exception as e:
            print("Error en update del serializer:", e)
            raise e

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name']  # o solo ['id', 'name']

class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all()
    )
    permission_details = PermissionSerializer(source='permissions', many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_details']
