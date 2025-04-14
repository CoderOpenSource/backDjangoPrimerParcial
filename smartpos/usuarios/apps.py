from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        post_migrate.connect(crear_roles_predefinidos, sender=self)

def crear_roles_predefinidos(sender, **kwargs):
    from django.contrib.auth.models import Group
    roles = ['Superadmin', 'Administrador', 'Vendedor']
    for nombre in roles:
        Group.objects.get_or_create(name=nombre)


