"""R1: carta pública, pedidos atómicos y transiciones de estado."""
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from .auth import requires_auth
from .extensions import db
from .models import ItemPedido, Pedido, Plato, Restaurante

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
    flash("Pedido creado correctamente.", "success")
    return redirect(url_for("carta.ver_pedido", pedido_id=pedido.id), code=303)


@bp.get("/pedidos")
@requires_auth("read:mis-pedidos")
def mis_pedidos(payload):
    pedidos = Pedido.query.filter_by(cliente=payload["sub"]).order_by(Pedido.fecha.desc()).all()
    return render_template("carta/mis_pedidos.html", pedidos=pedidos)


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
    return render_template("carta/pedido.html", pedido=pedido)


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
    return redirect(url_for("carta.ver_pedido", pedido_id=pedido_id), code=303)


@bp.get("/cocina")
@requires_auth("read:pedidos")
def cocina(payload):
    pedidos = Pedido.query.filter(Pedido.estado.in_([
        Pedido.PENDIENTE, Pedido.EN_PREPARACION, Pedido.LISTO
    ])).order_by(Pedido.fecha).all()
    return render_template("carta/cocina.html", pedidos=pedidos,
                           puede_avanzar="update:pedidos" in payload["permissions"])


SIGUIENTE = {
    Pedido.PENDIENTE: Pedido.EN_PREPARACION,
    Pedido.EN_PREPARACION: Pedido.LISTO,
    Pedido.LISTO: Pedido.ENTREGADO,
}


@bp.post("/cocina/pedidos/<int:pedido_id>/avanzar")
@requires_auth("update:pedidos")
def avanzar(payload, pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)
    anterior = pedido.estado
    siguiente = SIGUIENTE.get(anterior)
    if siguiente is None:
        abort(400, "El pedido no admite más avances.")
    try:
        # Evita que dos cocineros avancen dos veces un mismo estado a la vez.
        modificados = Pedido.query.filter_by(id=pedido_id, estado=anterior).update(
            {Pedido.estado: siguiente}, synchronize_session=False)
        if modificados != 1:
            db.session.rollback()
            abort(409, "Otro usuario cambió el estado; actualiza la página.")
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
    return redirect(url_for("carta.cocina"), code=303)
