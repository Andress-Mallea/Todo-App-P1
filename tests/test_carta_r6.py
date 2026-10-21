"""Las seis pruebas obligatorias de R6, según practico.pdf."""
from decimal import Decimal

from app.extensions import db
from app.models import ItemPedido, Pedido, Plato, Restaurante


def enviar_pedido(client, plato_id=1, cantidad=2, **extra):
    datos = {"plato_id": str(plato_id), "cantidad": str(cantidad), **extra}
    return client.post("/restaurantes/1/pedidos", data=datos)


def crear_pedido_de_prueba(cliente="auth0|cliente_a", estado=Pedido.PENDIENTE):
    pedido = Pedido(cliente=cliente, restaurante_id=1, estado=estado, total=Decimal("25.00"))
    db.session.add(pedido)
    db.session.flush()
    db.session.add(ItemPedido(pedido_id=pedido.id, plato_id=1, cantidad=1,
                              precio_unitario=Decimal("25.00")))
    db.session.commit()
    return pedido.id


def test_01_sin_sesion_no_se_crea_pedido(app, client):
    respuesta = enviar_pedido(client)
    assert respuesta.status_code in (302, 303, 401)
    with app.app_context():
        assert Pedido.query.count() == 0
        assert ItemPedido.query.count() == 0


def test_02_cliente_no_puede_avanzar_estado(app, client, entrar):
    with app.app_context():
        pedido_id = crear_pedido_de_prueba()
    entrar("cliente_a")
    respuesta = client.post(f"/cocina/pedidos/{pedido_id}/avanzar")
    assert respuesta.status_code == 403
    with app.app_context():
        assert db.session.get(Pedido, pedido_id).estado == Pedido.PENDIENTE


def test_03_precio_inventado_se_ignora(app, client, entrar):
    entrar("cliente_a")
    respuesta = enviar_pedido(client, precio="0.01", precio_unitario="0.01", total="0.01")
    assert respuesta.status_code == 303
    with app.app_context():
        pedido = Pedido.query.one()
        item = ItemPedido.query.one()
        assert pedido.cliente == "auth0|cliente_a"
        assert pedido.total == Decimal("50.00")
        assert item.precio_unitario == Decimal("25.00")
        assert item.cantidad == 2


def test_04_plato_no_disponible_revierte_todo(app, client, entrar):
    entrar("cliente_a")
    with app.app_context():
        agotado = Plato.query.filter_by(nombre="Agotado").one()
        agotado_id = agotado.id
    respuesta = enviar_pedido(client, plato_id=agotado_id)
    assert respuesta.status_code == 400
    with app.app_context():
        assert Pedido.query.count() == 0
        assert ItemPedido.query.count() == 0


def test_05_pedido_ajeno_devuelve_404(app, client, entrar):
    with app.app_context():
        pedido_id = crear_pedido_de_prueba(cliente="auth0|cliente_a")
    entrar("cliente_b")
    respuesta = client.get(f"/pedidos/{pedido_id}")
    assert respuesta.status_code == 404


def test_06_cocina_no_retrocede_listo_a_pendiente(app, client, entrar):
    with app.app_context():
        pedido_id = crear_pedido_de_prueba(estado=Pedido.LISTO)
    entrar("cocina")
    # La ruta no acepta elegir estado: solo avanza según el mapa SIGUIENTE.
    respuesta = client.post(f"/cocina/pedidos/{pedido_id}/avanzar", data={"estado": "pendiente"})
    assert respuesta.status_code == 303
    with app.app_context():
        assert db.session.get(Pedido, pedido_id).estado == Pedido.ENTREGADO
        assert db.session.get(Pedido, pedido_id).estado != Pedido.PENDIENTE


def test_07_cocina_no_ve_ni_avanza_pedido_ajeno(app, client, entrar):
    # Un pedido en el restaurante 2 no pertenece al empleado del restaurante 1.
    with app.app_context():
        otro = Restaurante(nombre="Otro restaurante", descripcion="")
        db.session.add(otro)
        db.session.flush()
        plato_ajeno = Plato(restaurante_id=otro.id, nombre="Plato ajeno",
                            descripcion="", precio=Decimal("15.00"), disponible=True)
        db.session.add(plato_ajeno)
        db.session.flush()
        pedido_ajeno = Pedido(cliente="auth0|cliente_b", restaurante_id=otro.id,
                              estado=Pedido.PENDIENTE, total=Decimal("15.00"))
        db.session.add(pedido_ajeno)
        db.session.flush()
        db.session.add(ItemPedido(pedido_id=pedido_ajeno.id,
                                  plato_id=plato_ajeno.id, cantidad=1,
                                  precio_unitario=Decimal("15.00")))
        db.session.commit()
        pedido_ajeno_id = pedido_ajeno.id

    entrar("cocina")
    respuesta_lista = client.get("/cocina")
    assert respuesta_lista.status_code == 200
    # Aseguramos que el pedido ajeno no figure en la cola de cocina.
    assert f"/cocina/pedidos/{pedido_ajeno_id}/avanzar" not in respuesta_lista.get_data(as_text=True)

    respuesta_avanzar = client.post(f"/cocina/pedidos/{pedido_ajeno_id}/avanzar")
    assert respuesta_avanzar.status_code == 404
    with app.app_context():
        assert db.session.get(Pedido, pedido_ajeno_id).estado == Pedido.PENDIENTE