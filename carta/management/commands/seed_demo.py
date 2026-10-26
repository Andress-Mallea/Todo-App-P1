"""Pobla 10.000 filas de demostración en 12 tablas de La Carta 2.0.

Preserva datos existentes, incluidos los 1.000 registros del seed anterior.
Las cuentas de prueba solo deben habilitarse en un entorno controlado.
Idempotente por identificadores estables (no elimina ni sobrescribe registros previos).
Uso: python manage.py seed_demo (invocado automáticamente por Docker Compose).
"""
import os
import secrets
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from werkzeug.security import generate_password_hash

from carta.models import (
    Categoria, Restaurante, Plato, Mesa, Promocion, PromocionPlato,
    Pedido, ItemPedido, Usuario, CuentaLocal, Cliente, Empleado,
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
    "Usuario": 1501,
    "CuentaLocal": 1501,
    "Cliente": 1200,
    "Empleado": 300,
    "Restaurante": 20,
    "Plato": 1398,
    "Categoria": 30,
    "Mesa": 500,
    "Promocion": 500,
    "PromocionPlato": 1000,
    "Pedido": 900,
    "ItemPedido": 1150,
}
assert sum(TARGETS.values()) == 10000

class Command(BaseCommand):
    help = "Crea hasta 10.000 filas demo repartidas entre 12 tablas sin tocar Auth0."

    @transaction.atomic
    def handle(self, *args, **options):
        created = {name: 0 for name in TARGETS}

        def get(model, lookup, defaults=None):
            obj, added = model.objects.get_or_create(
                **lookup, defaults=defaults or {}
            )
            created[model.__name__] += int(added)
            return obj

        # Categorías: conservar las 6 conocidas y añadir 24 de demostración.
        categorias = {
            name: get(Categoria, {"nombre": name}, {"descripcion": description})
            for name, description in CATEGORIAS
        }
        for n in range(1, 25):
            name = f"Categoría demo {n:02d}"
            categorias[name] = get(Categoria, {"nombre": name}, {
                "descripcion": "Categoría adicional de demostración."
            })
        nombres_categorias = list(categorias)
        estados = [Pedido.PENDIENTE, Pedido.EN_PREPARACION, Pedido.LISTO,
                   Pedido.ENTREGADO, Pedido.CANCELADO]

        # Conservar los cuatro restaurantes originales y sus menús.
        restaurantes_datos = list(RESTAURANTES)
        for n in range(5, 21):
            restaurantes_datos.append((
                f"Restaurante demo {n:02d}",
                "Restaurante generado para el examen.",
                [],
            ))

        restaurantes = []
        pedidos_adicionales = 0
        items_adicionales = 0
        for r_idx, (rest_name, rest_desc, base_menu) in enumerate(restaurantes_datos, 1):
            restaurante = get(Restaurante, {"nombre": rest_name}, {
                "descripcion": rest_desc
            })
            restaurantes.append(restaurante)
            platos = []

            for plato_name, description, price, cat_name in base_menu:
                platos.append(get(Plato, {
                    "restaurante": restaurante, "nombre": plato_name
                }, {
                    "descripcion": description, "precio": Decimal(price),
                    "disponible": True, "categoria": categorias[cat_name],
                }))

            # 120 platos en los 4 originales; 1.278 en los otros 16.
            # Se conservan los 24 Especial demo 01..24 de cada restaurante original.
            cantidad_platos = 30 if r_idx <= 4 else (79 if r_idx in (5, 6) else 80)
            for n in range(1, cantidad_platos - len(base_menu) + 1):
                name = (f"Especial demo {n:02d} - {rest_name}" if r_idx <= 4
                        else f"Plato demo {n:03d} - {rest_name}")
                categoria = nombres_categorias[(n + r_idx - 2) % len(nombres_categorias)]
                precio = Decimal(18 + (r_idx * 7 + n * 3) % 65).quantize(Decimal("0.01"))
                platos.append(get(Plato, {
                    "restaurante": restaurante, "nombre": name
                }, {
                    "descripcion": "Plato de demostración para el examen.",
                    "precio": precio, "disponible": True, "categoria": categorias[categoria],
                }))

            # 25 mesas por restaurante = 500. Las primeras 20 ya existían.
            for numero in range(1, 26):
                get(Mesa, {"restaurante": restaurante, "numero": numero}, {
                    "capacidad": [2, 4, 4, 6, 8][(numero - 1) % 5],
                    "activa": True,
                })

            # 25 promociones por restaurante = 500; dos platos por promoción = 1000.
            # Las primeras 10 promociones de los restaurantes originales no se alteran.
            for promo_idx in range(1, 26):
                if promo_idx == 1:
                    nombre = "Promo bienvenida"
                    descuento = Decimal("10.00")
                    posiciones = [0, 1]
                elif promo_idx == 2:
                    nombre = "Especial de la casa"
                    descuento = Decimal("15.00")
                    posiciones = [2, 3]
                else:
                    nombre = f"Promo demo {promo_idx:02d}"
                    descuento = Decimal(5 + promo_idx)
                    if r_idx <= 4 and promo_idx <= 10:
                        posiciones = [(promo_idx * 2) % 30, (promo_idx * 2 + 1) % 30]
                    else:
                        posiciones = [(promo_idx * 2) % len(platos),
                                      (promo_idx * 2 + 1) % len(platos)]
                promo = get(Promocion, {"restaurante": restaurante, "nombre": nombre}, {
                    "descripcion": "Promoción de demostración para La Carta.",
                    "porcentaje_descuento": descuento, "activa": True,
                })
                for pos in posiciones:
                    get(PromocionPlato, {"promocion": promo, "plato": platos[pos]})

            # Conservar los 220 pedidos originales (55 en cada uno de los primeros 4).
            # Nuevos: 8 restaurantes con 43 pedidos + 8 con 42 = 680.
            cantidad_pedidos = 55 if r_idx <= 4 else (43 if r_idx <= 12 else 42)
            for numero in range(1, cantidad_pedidos + 1):
                marker = f"seed-demo:restaurante-{r_idx}:pedido-{numero}"
                if r_idx <= 4:
                    if numero == 1:
                        estado = Pedido.PENDIENTE
                        detalles = [(0, 2), (4, 1)]
                    elif numero == 2:
                        estado = Pedido.LISTO
                        detalles = [(1, 1), (5, 2)]
                    else:
                        estado = estados[(numero + r_idx) % len(estados)]
                        primero = (numero * 3 + r_idx) % 30
                        segundo = (primero + 7) % 30
                        detalles = [(primero, 1 + numero % 3),
                                    (segundo, 1 + numero % 2)]
                        serial = (r_idx - 1) * 53 + (numero - 3)
                        if serial < 10:
                            detalles.append(((primero + 13) % 30, 1))
                else:
                    estado = estados[(numero + r_idx) % len(estados)]
                    primero = (numero * 3 + r_idx) % len(platos)
                    detalles = [(primero, 1 + numero % 3)]
                    # 20 ítems adicionales, sobre los primeros 20 pedidos nuevos.
                    if pedidos_adicionales < 20:
                        detalles.append(((primero + 7) % len(platos), 1))
                    pedidos_adicionales += 1
                    items_adicionales += len(detalles)

                total = sum(
                    (platos[pos].precio * cantidad for pos, cantidad in detalles),
                    Decimal("0.00")
                )
                pedido = get(Pedido, {"cliente": marker, "restaurante": restaurante}, {
                    "estado": estado, "total": total,
                })
                for pos, cantidad in detalles:
                    get(ItemPedido, {"pedido": pedido, "plato": platos[pos]}, {
                        "cantidad": cantidad,
                        "precio_unitario": platos[pos].precio,
                    })

        assert pedidos_adicionales == 680
        assert items_adicionales == 700

        # Tres cuentas conocidas para demostrar el login. Contraseñas desde .env.
        cuentas_demo = [
            ("cliente_demo", CuentaLocal.ROL_CLIENTE, "Cliente", "Demo",
             "SEED_CLIENTE_PASSWORD"),
            ("cocina_demo", CuentaLocal.ROL_COCINA, "Cocinero", "Demo",
             "SEED_COCINA_PASSWORD"),
            ("admin_demo", CuentaLocal.ROL_ADMIN, "Administrador", "Demo",
             "SEED_ADMIN_PASSWORD"),
        ]
        contrasenas = {}
        for username, _rol, _nombre, _apellido, var in cuentas_demo:
            password = os.environ.get(var, "")
            if len(password) < 12:
                raise CommandError(
                    f"Define {var} con una contraseña de al menos 12 caracteres."
                )
            contrasenas[username] = password

        # 1199 clientes más y 299 cocineros más, sin crear administradores en masa.
        for n in range(1, 1200):
            cuentas_demo.append((f"cliente_demo_{n:04d}", CuentaLocal.ROL_CLIENTE,
                                 "Cliente", f"Demo {n:04d}", None))
        for n in range(1, 300):
            cuentas_demo.append((f"cocina_demo_{n:04d}", CuentaLocal.ROL_COCINA,
                                 "Cocinero", f"Demo {n:04d}", None))
        assert len(cuentas_demo) == 1501

        for n, (username, rol, nombre, apellido, password_env) in enumerate(cuentas_demo):
            identity = f"local-seed:{username}"
            usuario = get(Usuario, {"auth0_sub": identity}, {
                "nombre": nombre, "apellido": apellido,
                "email": f"{username}@example.invalid",
            })

            cuenta = CuentaLocal.objects.filter(username=username).first()
            if cuenta is None:
                # Las cuentas sintéticas tienen contraseña aleatoria NO publicada.
                # Solamente las 3 cuentas iniciales son utilizables como demo.
                pwd = contrasenas[username] if password_env else secrets.token_urlsafe(48)
                cuenta = CuentaLocal.objects.create(
                    username=username,
                    password_hash=generate_password_hash(
                        pwd, method="pbkdf2:sha256:100000"
                    ),
                    rol=rol,
                    usuario=usuario,
                )
                created["CuentaLocal"] += 1
            elif cuenta.usuario_id != usuario.id:
                raise CommandError(
                    f"La cuenta '{username}' ya existe pero no está asociada al "
                    "perfil del seed. No se modificó su identidad."
                )

            if rol == CuentaLocal.ROL_CLIENTE:
                get(Cliente, {"usuario": usuario}, {
                    "direccion": "Dirección de demostración",
                })
            elif rol == CuentaLocal.ROL_COCINA:
                # Distribuir empleados entre los 20 restaurantes.
                restaurante = restaurantes[(n - 1) % len(restaurantes)]
                if username == "cocina_demo":
                    restaurante = restaurantes[0]  # Dragón Pai
                get(Empleado, {"usuario": usuario}, {
                    "cargo": "Cocinero", "restaurante": restaurante,
                    "activo": True,
                })

        modelos = [Usuario, CuentaLocal, Cliente, Empleado, Restaurante, Plato,
                   Categoria, Mesa, Promocion, PromocionPlato, Pedido, ItemPedido]
        actual = {model.__name__: model.objects.count() for model in modelos}
        esperado = sum(TARGETS.values())
        self.stdout.write(self.style.SUCCESS(
            f"Poblado demo preparado: {esperado} filas en 12 tablas "
            "(más cualquier dato previo ajeno al seed)."
        ))
        self.stdout.write(f"Nuevas filas en esta ejecución: {created}")
        self.stdout.write(f"Conteos actuales por tabla: {actual}")
        self.stdout.write(
            "Los registros de usuarios Auth0 y los datos previos no se eliminan."
        )
