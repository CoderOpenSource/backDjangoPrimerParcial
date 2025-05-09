# Generated by Django 4.2 on 2025-04-16 03:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('productos', '0002_categoria_foto_perfil_subcategoria_foto_perfil'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductoFavorito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_agregado', models.DateTimeField(auto_now_add=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to='productos.producto')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favoritos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Producto Favorito',
                'verbose_name_plural': 'Productos Favoritos',
                'unique_together': {('usuario', 'producto')},
            },
        ),
    ]
