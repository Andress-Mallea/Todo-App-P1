"""R1: carta pública, pedidos atómicos y transiciones de estado."""
from decimal import Decimal

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from .auth import requires_auth
from .extensions import db
from .models import Empleado, ItemPedido, Pedido, Plato, Restaurante, Usuario, CuentaLocal

bp = Blueprint("carta", __name__)


@bp.get("/restaurantes")
def restaurantes():
    return render_template("carta/restaurantes.html", restaurantes=Restaurante.query.order_by(Restaurante.nombre).all())


@bp.get("/restaurantes/<int:restaurante_id>")
def detalle_restaurante(restaurante_id):
    restaurante = db.get_or_404(Restaurante, restaurante_id)
    platos = Plato.query.filter_by(restaurante_id=restaurante_id).order_by(Plato.nombre).all()
    return render_template("carta/detalle.html", restaurante=restaurante, platos=platos)


@bp.post("/restaurantes/<int:restaurante_id>/pedidos")
@requires_auth("create:pedidos")
def crear_pedido(payload, restaurante_id):
    restaurante = db.get_or_404(Restaurante, restaurante_id)
    # Solo se reciben ids de platos y cantidades; NUNCA se aceptan precios ni totales.
    ids = request.form.getlist("plato_id")
    cantidades = request.form.getlist("cantidad")
    if not ids or len(ids) != len(cantidades):
        abort(400, "Se requiere al menos un plato y su cantidad.")
    cantidades_por_plato = {}
    for raw_id, raw_qty in zip(ids, cantidades):
        try:
            plato_id = int(raw_id)
            cantidad = int(raw_qty)
        except (ValueError, TypeError):
            abort(400, "Plato o cantidad inválidos.")
        if plato_id <= 0 or not 0 <= cantidad <= 20:
            abort(400, "La cantidad debe ser un entero entre 0 y 20.")
        if cantidad == 0:
            continue
        cantidades_por_plato[plato_id] = cantidades_por_plato.get(plato_id, 0) + cantidad
        if cantidades_por_plato[plato_id] > 20:
            abort(400, "Máximo 20 unidades por plato.")

    if not cantidades_por_plato:
        abort(400, "Selecciona al menos un plato con cantidad positiva.")

    # Verificar todos los datos antes de insertar una fila.
    lineas = []
    total = Decimal("0.00")
    for plato_id, cantidad in cantidades_por_plato.items():
        plato = db.session.get(Plato, plato_id)
        if plato is None:
            abort(404, "Plato inexistente.")
        if plato.restaurante_id != restaurante.id or not plato.disponible:
            abort(400, "Plato no disponible o de otro restaurante.")
        precio = Decimal(plato.precio)
        lineas.append((plato, cantidad, precio))
        total += precio * cantidad

    try:
        pedido = Pedido(cliente=payload["sub"], restaurante_id=restaurante.id,
                        estado=Pedido.PENDIENTE, total=total)
        db.session.add(pedido)
        db.session.flush()  # Obtiene el id; todavía no confirma nada.
        for plato, cantidad, precio in lineas:
            db.session.add(ItemPedido(pedido_id=pedido.id, plato_id=plato.id,
                                      cantidad=cantidad, precio_unitario=precio))
        db.session.commit()  # Todas las filas se confirman juntas.
    except SQLAlchemyError:
        db.session.rollback()  # Nada queda a medias.
        raise
    # Para JWT local devolvemos JSON, sin redirección.
    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "message": "Pedido creado correctamente.",
            "pedido_id": pedido.id,
            "url": url_for("carta.ver_pedido", pedido_id=pedido.id)
        }), 201

    # Auth0 mantiene el comportamiento original.
    flash("Pedido creado correctamente.", "success")
    return redirect(
        url_for("carta.ver_pedido", pedido_id=pedido.id),
        code=303
    )


@bp.get("/pedidos")
@requires_auth("read:mis-pedidos")
def mis_pedidos(payload):
    pedidos = (
        Pedido.query
        .filter_by(cliente=payload["sub"])
        .order_by(Pedido.fecha.desc())
        .all()
    )

    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "pedidos": [
                {
                    "id": p.id,
                    "estado": p.estado,
                    "total": str(p.total),
                    "fecha": p.fecha.isoformat()
                }
                for p in pedidos
            ]
        })

    return render_template(
        "carta/mis_pedidos.html",
        pedidos=pedidos
    )
@bp.get("/mis-pedidos-local")
def mis_pedidos_local():
    return render_template("carta/mis_pedidos_local.html")

def pedido_del_cliente(pedido_id, sub):
    # 404 evita revelar la existencia de pedidos de otros clientes.
    pedido = Pedido.query.filter_by(id=pedido_id, cliente=sub).first()
    if pedido is None:
        abort(404)
    return pedido


@bp.get("/pedidos/<int:pedido_id>")
@requires_auth("read:mis-pedidos")
def ver_pedido(payload, pedido_id):
    pedido = pedido_del_cliente(pedido_id, payload["sub"])

    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "pedido": {
                "id": pedido.id,
                "estado": pedido.estado,
                "total": str(pedido.total),
                "fecha": pedido.fecha.isoformat(),
                "restaurante": pedido.restaurante.nombre,
                "items": [
                    {
                        "plato": item.plato.nombre,
                        "cantidad": item.cantidad,
                        "precio_unitario": str(item.precio_unitario),
                        "subtotal": str(
                            item.precio_unitario * item.cantidad
                        )
                    }
                    for item in pedido.items
                ]
            }
        })

    # Auth0 conserva su página tradicional.
    return render_template("carta/pedido.html", pedido=pedido)
@bp.get("/mis-pedidos-local/<int:pedido_id>")
def detalle_pedido_local(pedido_id):
    return render_template(
        "carta/pedido_local.html",
        pedido_id=pedido_id
    )

@bp.post("/pedidos/<int:pedido_id>/cancelar")
@requires_auth("read:mis-pedidos")
def cancelar(payload, pedido_id):
    pedido_del_cliente(pedido_id, payload["sub"])
    # Actualización condicional: solo cancela si todavía está pendiente.
    try:
        modificados = Pedido.query.filter_by(id=pedido_id, cliente=payload["sub"],
                                            estado=Pedido.PENDIENTE).update(
            {Pedido.estado: Pedido.CANCELADO}, synchronize_session=False)
        if modificados != 1:
            db.session.rollback()
            abort(400, "Solo se pueden cancelar pedidos pendientes.")
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "message": "Pedido cancelado correctamente.",
            "pedido_id": pedido_id,
            "estado": Pedido.CANCELADO
        }), 200
    return redirect(url_for("carta.ver_pedido", pedido_id=pedido_id), code=303)


def restaurante_del_cocinero(payload):
    """
    Obtiene el restaurante del empleado autenticado.

    Auth0: busca al empleado mediante auth0_sub.
    JWT local: busca al empleado mediante CuentaLocal -> Usuario.

    Solo permite empleados activos con restaurante asignado.
    """
    sub = payload["sub"]

    if sub.startswith("local:"):
        # Identidad local verificada previamente por requires_auth.
        try:
            cuenta_id = int(sub.split(":", 1)[1])
        except ValueError:
            abort(403, "Identificador de cuenta local inválido.")

        empleado = (
            Empleado.query
            .join(Usuario, Empleado.usuario_id == Usuario.id)
            .join(CuentaLocal, CuentaLocal.usuario_id == Usuario.id)
            .filter(
                CuentaLocal.id == cuenta_id,
                CuentaLocal.rol == "cocina",
                Empleado.activo.is_(True),
            )
            .first()
        )

    else:
        # Se conserva la identificación original mediante Auth0.
        empleado = (
            Empleado.query
            .join(Usuario, Empleado.usuario_id == Usuario.id)
            .filter(
                Usuario.auth0_sub == sub,
                Empleado.activo.is_(True),
            )
            .first()
        )

    if empleado is None or empleado.restaurante_id is None:
        abort(
            403,
            "No tienes un restaurante de cocina asignado "
            "o tu perfil de empleado está inactivo."
        )

    return empleado.restaurante_id


@bp.get("/cocina")
@requires_auth("read:pedidos")
def cocina(payload):
    puede_avanzar = "update:pedidos" in payload["permissions"]

    pedidos_query = Pedido.query.filter(
        Pedido.estado.in_([
            Pedido.PENDIENTE,
            Pedido.EN_PREPARACION,
            Pedido.LISTO
        ])
    )

    if puede_avanzar:
        restaurante_id = restaurante_del_cocinero(payload)

        pedidos_query = pedidos_query.filter_by(
            restaurante_id=restaurante_id
        )

    pedidos = pedidos_query.order_by(Pedido.fecha).all()

    # Respuesta para usuarios JWT locales
    if payload["sub"].startswith("local:"):
        return jsonify({
            "pedidos": [
                {
                    "id": pedido.id,
                    "restaurante": pedido.restaurante.nombre,
                    "estado": pedido.estado,
                    "items": [
                        {
                            "plato": item.plato.nombre,
                            "cantidad": item.cantidad
                        }
                        for item in pedido.items
                    ]
                }
                for pedido in pedidos
            ],
            "puede_avanzar": puede_avanzar
        }), 200

    # Se conserva el comportamiento de Auth0
    return render_template(
        "carta/cocina.html",
        pedidos=pedidos,
        puede_avanzar=puede_avanzar
    )


SIGUIENTE = {
    Pedido.PENDIENTE: Pedido.EN_PREPARACION,
    Pedido.EN_PREPARACION: Pedido.LISTO,
    Pedido.LISTO: Pedido.ENTREGADO,
}


@bp.post("/cocina/pedidos/<int:pedido_id>/avanzar")
@requires_auth("update:pedidos")
def avanzar(payload, pedido_id):
    restaurante_id = restaurante_del_cocinero(payload)
    # El filtro por restaurante es obligatorio en la consulta Y en el UPDATE.
    # Un ID de otro restaurante (o inexistente) responde 404.
    pedido = Pedido.query.filter_by(id=pedido_id, restaurante_id=restaurante_id).first_or_404()
    anterior = pedido.estado
    siguiente = SIGUIENTE.get(anterior)
    if siguiente is None:
        abort(400, "El pedido no admite más avances.")
    try:
        modificados = Pedido.query.filter_by(
            id=pedido_id, restaurante_id=restaurante_id, estado=anterior
        ).update({Pedido.estado: siguiente}, synchronize_session=False)
        if modificados != 1:
            db.session.rollback()
            abort(409, "Otro usuario cambió el estado; actualiza la página.")
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "message": "Estado del pedido actualizado correctamente.",
            "pedido_id": pedido_id,
            "estado_anterior": anterior,
            "estado_actual": siguiente
        }), 200

    return redirect(url_for("carta.cocina"), code=303)
@bp.get("/cocina-local")
def cocina_local():
    # Solo entrega la interfaz.
    # Los pedidos se obtienen desde /cocina, que exige autenticación.
    return render_template("carta/cocina_local.html")