from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Restaurante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Plato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(blank=True)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
                ('disponible', models.BooleanField(default=True)),
                ('restaurante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='platos', to='carta.restaurante')),
            ],
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente', models.CharField(max_length=255)),
                ('estado', models.CharField(choices=[('pendiente','Pendiente'),('en_preparacion','En preparación'),('listo','Listo'),('entregado','Entregado'),('cancelado','Cancelado')], default='pendiente', max_length=20)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('restaurante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pedidos', to='carta.restaurante')),
            ],
        ),
        migrations.CreateModel(
            name='ItemPedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='carta.pedido')),
                ('plato', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items_pedido', to='carta.plato')),
            ],
        ),
        migrations.AddConstraint(model_name='plato', constraint=models.CheckConstraint(check=Q(precio__gte=0), name='carta_plato_precio_no_negativo')),
        migrations.AddConstraint(model_name='pedido', constraint=models.CheckConstraint(check=Q(estado__in=['pendiente','en_preparacion','listo','entregado','cancelado']), name='carta_pedido_estado_valido')),
        migrations.AddConstraint(model_name='pedido', constraint=models.CheckConstraint(check=Q(total__gte=0), name='carta_pedido_total_no_negativo')),
        migrations.AddConstraint(model_name='itempedido', constraint=models.CheckConstraint(check=Q(cantidad__gt=0), name='carta_item_cantidad_positiva')),
        migrations.AddConstraint(model_name='itempedido', constraint=models.CheckConstraint(check=Q(precio_unitario__gte=0), name='carta_item_precio_no_negativo')),
    ]
