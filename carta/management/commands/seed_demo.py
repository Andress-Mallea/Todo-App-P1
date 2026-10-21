"""Datos de demostración para La Carta 2.0. No crea perfiles Auth0.

Uso: python manage.py seed_demo
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from carta.models import (
    Categoria, Restaurante, Plato, Mesa, Promocion,
    PromocionPlato, Pedido, ItemPedido,
)


CATEGORIAS = [
    ("Entradas", "Para comenzar la comida."),
    ("Platos principales", "Especialidades de la casa."),
    ("Hamburguesas", "Hamburguesas artesanales."),
    ("Pizzas", "Pizzas recién horneadas."),
    ("Bebidas", "Bebidas frías y calientes."),
    ("Postres", "Opciones dulces."),
]

# Cada plato: (nombre, descripción, precio en BOB, categoría)
RESTAURANTES = [
    (
        "Dragón Pai", "Comida asiática y especialidades de la casa.",
        [
            ("Ramen especial", "Fideos, caldo concentrado, huevo y verduras.", "49.00", "Platos principales"),
            ("Pollo teriyaki", "Pollo glaseado con arroz y vegetales.", "45.00", "Platos principales"),
            ("Gyozas", "Empanadillas al vapor con salsa de soya.", "28.00", "Entradas"),
            ("Arroz frito", "Arroz salteado con vegetales y huevo.", "34.00", "Platos principales"),
            ("Té helado", "Té con limón y hielo.", "14.00", "Bebidas"),
            ("Mochi", "Postre japonés de arroz dulce.", "20.00", "Postres"),
        ],
    ),
    (
        "La Parrilla Cruceña", "Carnes a la parrilla y platos bolivianos.",
        [
            ("Pique macho", "Carne, papas, salchicha, huevo y verduras.", "65.00", "Platos principales"),
            ("Bife a la parrilla", "Corte de res con guarnición.", "78.00", "Platos principales"),
            ("Chorizo parrillero", "Chorizo artesanal con llajua.", "29.00", "Entradas"),
            ("Pollo a la brasa", "Pollo especiado con papas y ensalada.", "48.00", "Platos principales"),
            ("Limonada", "Limonada natural.", "15.00", "Bebidas"),
            ("Flan casero", "Flan con caramelo.", "22.00", "Postres"),
        ],
    ),
    (
        "Pizza Central", "Pizzas artesanales y bebidas.",
        [
            ("Pizza margarita", "Tomate, mozzarella y albahaca.", "58.00", "Pizzas"),
            ("Pizza pepperoni", "Mozzarella y pepperoni.", "66.00", "Pizzas"),
            ("Pizza cuatro quesos", "Selección de cuatro quesos.", "72.00", "Pizzas"),
            ("Pan de ajo", "Pan horneado con ajo y mantequilla.", "24.00", "Entradas"),
            ("Gaseosa", "Bebida gaseosa individual.", "12.00", "Bebidas"),
            ("Brownie", "Brownie de chocolate.", "25.00", "Postres"),
        ],
    ),
    (
        "Burger House", "Hamburguesas, acompañamientos y batidos.",
        [
            ("Hamburguesa clásica", "Res, queso, lechuga y tomate.", "42.00", "Hamburguesas"),
            ("Hamburguesa doble", "Doble carne, queso y salsa especial.", "59.00", "Hamburguesas"),
            ("Hamburguesa vegetariana", "Medallón vegetal y vegetales frescos.", "43.00", "Hamburguesas"),
            ("Papas fritas", "Papas crocantes con salsa.", "19.00", "Entradas"),
            ("Batido de chocolate", "Batido cremoso de chocolate.", "21.00", "Bebidas"),
            ("Cheesecake", "Tarta de queso con frutos rojos.", "27.00", "Postres"),
        ],
    ),
]


class Command(BaseCommand):
    help = "Carga datos de demostración idempotentes sin crear Usuario, Cliente ni Empleado."

    @transaction.atomic
    def handle(self, *args, **options):
        categorias = {}
        for nombre, descripcion in CATEGORIAS:
            obj, _ = Categoria.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": descripcion}
            )
            categorias[nombre] = obj

        resumen = {"restaurantes": 0, "platos": 0, "mesas": 0,
                   "promociones": 0, "promocion_plato": 0,
                   "pedidos": 0, "items": 0}

        for idx, (nombre, descripcion, platos_data) in enumerate(RESTAURANTES, start=1):
            restaurante, creado = Restaurante.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": descripcion}
            )
            resumen["restaurantes"] += int(creado)
            platos = []
            for plato_nombre, plato_descripcion, precio, categoria_nombre in platos_data:
                plato, creado = Plato.objects.get_or_create(
                    restaurante=restaurante,
                    nombre=plato_nombre,
                    defaults={
                        "descripcion": plato_descripcion,
                        "precio": Decimal(precio),
                        "disponible": True,
                        "categoria": categorias[categoria_nombre],
                    },
                )
                resumen["platos"] += int(creado)
                platos.append(plato)

            for numero, capacidad in [(1, 2), (2, 4), (3, 4), (4, 6), (5, 8)]:
                _, creado = Mesa.objects.get_or_create(
                    restaurante=restaurante, numero=numero,
                    defaults={"capacidad": capacidad, "activa": True},
                )
                resumen["mesas"] += int(creado)

            for nombre_promo, descuento, indices in [
                ("Promo bienvenida", "10.00", (0, 1)),
                ("Especial de la casa", "15.00", (2, 3)),
            ]:
                promo, creado = Promocion.objects.get_or_create(
                    restaurante=restaurante, nombre=nombre_promo,
                    defaults={
                        "descripcion": "Promoción de demostración para la carta.",
                        "porcentaje_descuento": Decimal(descuento),
                        "activa": True,
                    },
                )
                resumen["promociones"] += int(creado)
                for indice_plato in indices:
                    _, creado = PromocionPlato.objects.get_or_create(
                        promocion=promo, plato=platos[indice_plato]
                    )
                    resumen["promocion_plato"] += int(creado)

            # Pedido.cliente es un CharField, no una FK a Usuario/Cliente.
            # Los identificadores seed-demo NO son usuarios reales de Auth0.
            # Se crean pedidos ficticios claramente identificados para la defensa.
            for numero_demo, estado, lineas in [
                (1, Pedido.PENDIENTE, [(0, 2), (4, 1)]),
                (2, Pedido.LISTO, [(1, 1), (5, 2)]),
            ]:
                marker = f"seed-demo:restaurante-{idx}:pedido-{numero_demo}"
                total = sum(
                    (platos[pos].precio * cantidad for pos, cantidad in lineas),
                    Decimal("0.00"),
                )
                pedido, creado = Pedido.objects.get_or_create(
                    cliente=marker,
                    restaurante=restaurante,
                    defaults={"estado": estado, "total": total},
                )
                resumen["pedidos"] += int(creado)
                if creado:
                    # Snapshot del precio: nunca depende de cambios posteriores del menú.
                    for pos, cantidad in lineas:
                        ItemPedido.objects.create(
                            pedido=pedido,
                            plato=platos[pos],
                            cantidad=cantidad,
                            precio_unitario=platos[pos].precio,
                        )
                        resumen["items"] += 1

        self.stdout.write(self.style.SUCCESS(
            "Seed completado. Registros nuevos: " +
            ", ".join(f"{clave}={valor}" for clave, valor in resumen.items())
        ))
        self.stdout.write(
            "Categorias totales usadas: 6. No se modificaron Usuario, Cliente ni Empleado."
        )
