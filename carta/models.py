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
