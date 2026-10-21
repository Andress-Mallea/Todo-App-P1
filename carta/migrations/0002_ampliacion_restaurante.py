import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):
    dependencies = [("carta", "0001_initial")]
    operations = [
        migrations.CreateModel(name="Usuario", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("auth0_sub", models.CharField(max_length=255, unique=True)),
            ("nombre", models.CharField(max_length=120, blank=True)),
            ("apellido", models.CharField(max_length=120, blank=True)),
            ("email", models.EmailField(max_length=254, blank=True)),
            ("telefono", models.CharField(max_length=30, blank=True)),
        ]),
        migrations.CreateModel(name="Categoria", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("nombre", models.CharField(max_length=100)),
            ("descripcion", models.TextField(blank=True)),
        ]),
        migrations.AddField(model_name="plato", name="categoria", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="platos", to="carta.categoria")),
        migrations.CreateModel(name="Cliente", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("direccion", models.CharField(max_length=255, blank=True)),
            ("fecha_registro", models.DateTimeField(default=django.utils.timezone.now)),
            ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_cliente", to="carta.usuario")),
        ]),
        migrations.CreateModel(name="Empleado", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("cargo", models.CharField(max_length=100)),
            ("fecha_contratacion", models.DateField(default=django.utils.timezone.localdate)),
            ("activo", models.BooleanField(default=True)),
            ("restaurante", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="empleados", to="carta.restaurante")),
            ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_empleado", to="carta.usuario")),
        ]),
        migrations.CreateModel(name="Mesa", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("numero", models.PositiveIntegerField()),
            ("capacidad", models.PositiveIntegerField()),
            ("activa", models.BooleanField(default=True)),
            ("restaurante", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mesas", to="carta.restaurante")),
        ]),
        migrations.CreateModel(name="Promocion", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("nombre", models.CharField(max_length=150)),
            ("descripcion", models.TextField(blank=True)),
            ("porcentaje_descuento", models.DecimalField(max_digits=5, decimal_places=2, default=0)),
            ("activa", models.BooleanField(default=True)),
            ("restaurante", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="promociones", to="carta.restaurante")),
        ]),
        migrations.CreateModel(name="PromocionPlato", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("plato", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="promociones_plato", to="carta.plato")),
            ("promocion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="platos_promocion", to="carta.promocion")),
        ]),
        migrations.AddConstraint(model_name="mesa", constraint=models.UniqueConstraint(fields=("restaurante", "numero"), name="carta_mesa_unica_por_rest")),
        migrations.AddConstraint(model_name="mesa", constraint=models.CheckConstraint(check=Q(capacidad__gt=0), name="carta_mesa_capacidad_positiva")),
        migrations.AddConstraint(model_name="mesa", constraint=models.CheckConstraint(check=Q(numero__gt=0), name="carta_mesa_numero_positivo")),
        migrations.AddConstraint(model_name="promocion", constraint=models.CheckConstraint(check=Q(porcentaje_descuento__gte=0) & Q(porcentaje_descuento__lte=100), name="carta_promo_descuento_rango")),
        migrations.AddConstraint(model_name="promocionplato", constraint=models.UniqueConstraint(fields=("promocion", "plato"), name="carta_promo_plato_unico")),
    ]
