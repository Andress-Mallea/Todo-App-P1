from django.db import models
from django.db.models import Q
from django.utils import timezone


class Restaurante(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Plato(models.Model):
    restaurante = models.ForeignKey(
        Restaurante, on_delete=models.PROTECT, related_name="platos"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    categoria = models.ForeignKey("Categoria", on_delete=models.SET_NULL, null=True, blank=True, related_name="platos")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(precio__gte=0), name="carta_plato_precio_no_negativo"
            ),
        ]

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    PENDIENTE = "pendiente"
    EN_PREPARACION = "en_preparacion"
    LISTO = "listo"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (EN_PREPARACION, "En preparación"),
        (LISTO, "Listo"),
        (ENTREGADO, "Entregado"),
        (CANCELADO, "Cancelado"),
    ]

    cliente = models.CharField(max_length=255)  # 'sub' del token Auth0
    restaurante = models.ForeignKey(
        Restaurante, on_delete=models.PROTECT, related_name="pedidos"
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)
    fecha = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(estado__in=[
                            "pendiente",
                            "en_preparacion",
                            "listo",
                            "entregado",
                            "cancelado",
                        ]),
                name="carta_pedido_estado_valido",
            ),
            models.CheckConstraint(
                check=Q(total__gte=0), name="carta_pedido_total_no_negativo"
            ),
        ]

    def __str__(self):
        return f"Pedido #{self.pk} ({self.estado})"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="items"
    )
    plato = models.ForeignKey(
        Plato, on_delete=models.PROTECT, related_name="items_pedido"
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(cantidad__gt=0), name="carta_item_cantidad_positiva"
            ),
            models.CheckConstraint(
                check=Q(precio_unitario__gte=0),
                name="carta_item_precio_no_negativo"
            ),
        ]

    def __str__(self):
        return f"{self.cantidad} x {self.plato_id}"


class Usuario(models.Model):
    auth0_sub = models.CharField(max_length=255, unique=True)
    nombre = models.CharField(max_length=120, blank=True)
    apellido = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nombre or self.email or self.auth0_sub


class Cliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_cliente")
    direccion = models.CharField(max_length=255, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Cliente: {self.usuario}"



class Empleado(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil_empleado"
    )

    restaurante = models.ForeignKey(
        Restaurante,
        on_delete=models.PROTECT,
        related_name="empleados",
        null=True,
        blank=True
    )

    cargo = models.CharField(max_length=100)

    fecha_contratacion = models.DateField(
        default=timezone.localdate
    )

    activo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario} - {self.cargo}"



class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Mesa(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT, related_name="mesas")
    numero = models.PositiveIntegerField()
    capacidad = models.PositiveIntegerField()
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["restaurante", "numero"], name="carta_mesa_unica_por_rest"),
            models.CheckConstraint(check=Q(capacidad__gt=0), name="carta_mesa_capacidad_positiva"),
            models.CheckConstraint(check=Q(numero__gt=0), name="carta_mesa_numero_positivo"),
        ]

    def __str__(self):
        return f"Mesa {self.numero} - {self.restaurante}"


class Promocion(models.Model):
    restaurante = models.ForeignKey(Restaurante, on_delete=models.PROTECT, related_name="promociones")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(porcentaje_descuento__gte=0) & Q(porcentaje_descuento__lte=100), name="carta_promo_descuento_rango"),
        ]

    def __str__(self):
        return self.nombre


class PromocionPlato(models.Model):
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE, related_name="platos_promocion")
    plato = models.ForeignKey(Plato, on_delete=models.PROTECT, related_name="promociones_plato")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["promocion", "plato"], name="carta_promo_plato_unico"),
        ]

    def __str__(self):
        return f"{self.promocion} - {self.plato}"
class CuentaLocal(models.Model):
    usuario = models.OneToOneField(
        "Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cuenta_local",
    )
    username = models.CharField(
        max_length=80,
        unique=True,
        db_index=True
    )

    password_hash = models.CharField(max_length=255)

    fecha_registro = models.DateTimeField(
        default=timezone.now
    )
    ROL_CLIENTE = "cliente"
    ROL_COCINA = "cocina"
    ROL_ADMIN = "admin"

    ROLES = [
        (ROL_CLIENTE, "Cliente"),
        (ROL_COCINA, "Cocina"),
        (ROL_ADMIN, "Administrador"),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default=ROL_CLIENTE,
    )
    def __str__(self):
        return self.username
