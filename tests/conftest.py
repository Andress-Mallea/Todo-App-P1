"""Fixtures aisladas para R6: sin Auth0 ni acceso a PostgreSQL real."""
import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from datetime import date
from app.models import Restaurante, Plato, Usuario, Empleado

CLIENTE = ["create:pedidos", "read:mis-pedidos"]
COCINA = ["read:pedidos", "update:pedidos"]

@pytest.fixture
def app(monkeypatch):
    # Sustituimos solo la verificación externa de JWT. Los decoradores, sus
    # comprobaciones de permisos y la sesión Flask se ejecutan de verdad.
    def verificar(token):
        perfiles = {
            "test-cliente-a": {"sub": "auth0|cliente_a", "permissions": CLIENTE},
            "test-cliente-b": {"sub": "auth0|cliente_b", "permissions": CLIENTE},
            "test-cocina": {"sub": "auth0|cocinero", "permissions": COCINA},
        }
        if token not in perfiles:
            from app.auth.errors import AuthError
            raise AuthError({"code": "invalid_token", "description": "Token inválido."}, 401)
        return perfiles[token]

    monkeypatch.setattr("app.auth.decorators.verify_decode_jwt", verificar)
    # current_user se llama al renderizar plantillas, así que también usa el doble.
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()  # PERMITIDO únicamente en la base aislada de pruebas.
        restaurante = Restaurante(nombre="Restaurante R6", descripcion="Pruebas")
        db.session.add(restaurante)
        db.session.flush()
        plato = Plato(restaurante_id=restaurante.id, nombre="Hamburguesa",
                      descripcion="", precio="25.00", disponible=True)
        no_disponible = Plato(restaurante_id=restaurante.id, nombre="Agotado",
                             descripcion="", precio="11.00", disponible=False)
        db.session.add_all([plato, no_disponible])
        # El cocinero simulado debe existir también como empleado activo.
        # La asociación se hace con el mismo `sub` del token de prueba.
        usuario_cocina = Usuario(auth0_sub="auth0|cocinero", nombre="Cocinero R6")
        db.session.add(usuario_cocina)
        db.session.flush()
        db.session.add(Empleado(
            usuario_id=usuario_cocina.id,
            restaurante_id=restaurante.id,
            cargo="Cocinero",
            fecha_contratacion=date.today(),
            activo=True,
        ))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def entrar(client):
    def _entrar(quien="cliente_a"):
        tokens = {"cliente_a": "test-cliente-a", "cliente_b": "test-cliente-b", "cocina": "test-cocina"}
        with client.session_transaction() as sess:
            sess["access_token"] = tokens[quien]
            sess["user"] = {"name": quien, "email": f"{quien}@example.test"}
    return _entrar