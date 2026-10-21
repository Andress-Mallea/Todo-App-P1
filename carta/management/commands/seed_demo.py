"""Poblacion de 1000 registros demostrativos en 8 tablas de carta.

No modifica Usuario, Cliente, Empleado ni las tablas del sistema Django.
Idempotente: ejecutar de nuevo no duplica registros identificados por el seed.
Uso: python manage.py seed_demo
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from carta.models import (
    Categoria, Restaurante, Plato, Mesa, Promocion, PromocionPlato,
    Pedido, ItemPedido,
)

CATEGORIAS = [
    ("Entradas", "Para comenzar la comida."),
    ("Platos principales", "Especialidades de la casa."),
    ("Hamburguesas", "Hamburguesas artesanales."),
    ("Pizzas", "Pizzas recien horneadas."),
    ("Bebidas", "Bebidas frias y calientes."),
    ("Postres", "Opciones dulces."),
]

RESTAURANTES = [
    ("Dragón Pai", "Comida asiatica y especialidades de la casa.", [
        ("Ramen especial", "Fideos, caldo, huevo y verduras.", "49.00", "Platos principales"),
        ("Pollo teriyaki", "Pollo glaseado con arroz.", "45.00", "Platos principales"),
        ("Gyozas", "Empanadillas al vapor.", "28.00", "Entradas"),
        ("Arroz frito", "Arroz salteado con verduras.", "34.00", "Platos principales"),
        ("Té helado", "Te con limon y hielo.", "14.00", "Bebidas"),
        ("Mochi", "Postre de arroz dulce.", "20.00", "Postres"),
    ]),
    ("La Parrilla Cruceña", "Carnes a la parrilla y platos bolivianos.", [
        ("Pique macho", "Carne, papas y verduras.", "65.00", "Platos principales"),
        ("Bife a la parrilla", "Corte de res con guarnicion.", "78.00", "Platos principales"),
        ("Chorizo parrillero", "Chorizo con llajua.", "29.00", "Entradas"),
        ("Pollo a la brasa", "Pollo con papas y ensalada.", "48.00", "Platos principales"),
        ("Limonada", "Limonada natural.", "15.00", "Bebidas"),
        ("Flan casero", "Flan con caramelo.", "22.00", "Postres"),
    ]),
    ("Pizza Central", "Pizzas artesanales y bebidas.", [
        ("Pizza margarita", "Tomate, mozzarella y albahaca.", "58.00", "Pizzas"),
        ("Pizza pepperoni", "Mozzarella y pepperoni.", "66.00", "Pizzas"),
        ("Pizza cuatro quesos", "Seleccion de cuatro quesos.", "72.00", "Pizzas"),
        ("Pan de ajo", "Pan horneado con ajo.", "24.00", "Entradas"),
        ("Gaseosa", "Bebida individual.", "12.00", "Bebidas"),
        ("Brownie", "Brownie de chocolate.", "25.00", "Postres"),
    ]),
    ("Burger House", "Hamburguesas, acompanamientos y batidos.", [
        ("Hamburguesa clásica", "Res, queso, lechuga y tomate.", "42.00", "Hamburguesas"),
        ("Hamburguesa doble", "Doble carne y queso.", "59.00", "Hamburguesas"),
        ("Hamburguesa vegetariana", "Medallon vegetal.", "43.00", "Hamburguesas"),
        ("Papas fritas", "Papas crocantes.", "19.00", "Entradas"),
        ("Batido de chocolate", "Batido cremoso.", "21.00", "Bebidas"),
        ("Cheesecake", "Tarta de queso.", "27.00", "Postres"),
    ]),
]

TARGETS = {
    "Categoria": 6, "Restaurante": 4, "Plato": 120, "Mesa": 80,
    "Promocion": 40, "PromocionPlato": 80, "Pedido": 220,
    "ItemPedido": 450,
}
assert sum(TARGETS.values()) == 1000


class Command(BaseCommand):
    help = "Crea 1000 registros demo en 8 tablas comerciales sin tocar perfiles Auth0."

    @transaction.atomic
    def handle(self, *args, **options):
        created = {key: 0 for key in TARGETS}

        def get(model, key, defaults=None):
            obj, added = model.objects.get_or_create(**key, defaults=defaults or {})
            created[model.__name__] += int(added)
            return obj

        categorias = {
            name: get(Categoria, {"nombre": name}, {"descripcion": description})
            for name, description in CATEGORIAS
        }
        nombres_categorias = list(categorias)
        estados = [Pedido.PENDIENTE, Pedido.EN_PREPARACION, Pedido.LISTO,
                   Pedido.ENTREGADO, Pedido.CANCELADO]

        for r_idx, (rest_name, rest_desc, base_menu) in enumerate(RESTAURANTES, start=1):
            restaurante = get(Restaurante, {"nombre": rest_name}, {"descripcion": rest_desc})
            platos = []

            # 6 del menu original + 24 variantes identificadas por un nombre fijo = 30.
            for plato_name, description, price, cat_name in base_menu:
                platos.append(get(Plato, {"restaurante": restaurante, "nombre": plato_name}, {
                    "descripcion": description, "precio": Decimal(price),
                    "disponible": True, "categoria": categorias[cat_name],
                }))
            for number in range(1, 25):
                category = nombres_categorias[(number - 1) % len(nombres_categorias)]
                price = Decimal(18 + (r_idx * 7 + number * 3) % 65).quantize(Decimal("0.01"))
                platos.append(get(Plato, {
                    "restaurante": restaurante,
                    "nombre": f"Especial demo {number:02d} - {rest_name}",
                }, {
                    "descripcion": "Variante de demostracion para el examen.",
                    "precio": price, "disponible": True,
                    "categoria": categorias[category],
                }))

            # 20 mesas por restaurante = 80.
            for numero in range(1, 21):
                get(Mesa, {"restaurante": restaurante, "numero": numero}, {
                    "capacidad": [2, 4, 4, 6, 8][(numero - 1) % 5],
                    "activa": True,
                })

            # 10 promociones por restaurante, dos platos por promocion = 80 relaciones.
            for promo_idx in range(1, 11):
                if promo_idx == 1:
                    promo_name = "Promo bienvenida"
                    descuento = Decimal("10.00")
                    indices = [0, 1]
                elif promo_idx == 2:
                    promo_name = "Especial de la casa"
                    descuento = Decimal("15.00")
                    indices = [2, 3]
                else:
                    promo_name = f"Promo demo {promo_idx:02d}"
                    descuento = Decimal(5 + promo_idx)
                    indices = [(promo_idx * 2) % 30, (promo_idx * 2 + 1) % 30]
                promo = get(Promocion, {"restaurante": restaurante, "nombre": promo_name}, {
                    "descripcion": "Promocion de demostracion para La Carta.",
                    "porcentaje_descuento": descuento,
                    "activa": True,
                })
                for pos in indices:
                    get(PromocionPlato, {"promocion": promo, "plato": platos[pos]})

            # 55 pedidos por restaurante; los 2 primeros conservan la version anterior.
            # 220 pedidos x 2 items + 10 items adicionales = 450.
            for order_number in range(1, 56):
                marker = f"seed-demo:restaurante-{r_idx}:pedido-{order_number}"
                if order_number == 1:
                    estado = Pedido.PENDIENTE
                    details = [(0, 2), (4, 1)]
                elif order_number == 2:
                    estado = Pedido.LISTO
                    details = [(1, 1), (5, 2)]
                else:
                    estado = estados[(order_number + r_idx) % len(estados)]
                    first = (order_number * 3 + r_idx) % 30
                    second = (first + 7) % 30
                    details = [(first, 1 + order_number % 3), (second, 1 + order_number % 2)]
                    serial = (r_idx - 1) * 53 + (order_number - 3)
                    if serial < 10:
                        details.append(((first + 13) % 30, 1))

                total = sum((platos[pos].precio * qty for pos, qty in details), Decimal("0.00"))
                pedido = get(Pedido, {"cliente": marker, "restaurante": restaurante}, {
                    "estado": estado, "total": total,
                })
                # Para los pedidos originales se respetan los items ya creados.
                for pos, qty in details:
                    get(ItemPedido, {"pedido": pedido, "plato": platos[pos]}, {
                        "cantidad": qty, "precio_unitario": platos[pos].precio,
                    })

        models = [Categoria, Restaurante, Plato, Mesa, Promocion,
                  PromocionPlato, Pedido, ItemPedido]
        actual = {model.__name__: model.objects.count() for model in models}
        seeded = sum(TARGETS.values())
        self.stdout.write(self.style.SUCCESS(
            f"Seed finalizado: conjunto de demostracion de {seeded} filas (sin perfiles Auth0)."
        ))
        self.stdout.write("Nuevas en esta ejecucion: " + str(created))
        self.stdout.write("Conteos actuales de las tablas (incluyen datos previos): " + str(actual))
        self.stdout.write("No se han creado ni alterado Usuario, Cliente ni Empleado.")
