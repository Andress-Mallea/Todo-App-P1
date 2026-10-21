"""Modelos SQLAlchemy sobre tablas administradas exclusivamente por Django.

No ejecutar db.create_all() ni Flask-Migrate sobre estas tablas en producción.
"""
from datetime import date, datetime, timezone

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


# Modelo antiguo: se conserva temporalmente porque las rutas existentes pueden importarlo.
class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Todo {self.id} {self.title!r} completed={self.completed}>"


class Restaurante(db.Model):
    __tablename__ = "carta_restaurante"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False, default="")

    platos = db.relationship("Plato", back_populates="restaurante")
    pedidos = db.relationship("Pedido", back_populates="restaurante")


class Plato(db.Model):
    __tablename__ = "carta_plato"

    id = db.Column(db.Integer, primary_key=True)
    restaurante_id = db.Column(
        db.Integer, db.ForeignKey("carta_restaurante.id"), nullable=False
    )
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False, default="")
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    disponible = db.Column(db.Boolean, nullable=False, default=True)

    restaurante = db.relationship("Restaurante", back_populates="platos")
    items_pedido = db.relationship("ItemPedido", back_populates="plato")


class Pedido(db.Model):
    __tablename__ = "carta_pedido"

    PENDIENTE = "pendiente"
    EN_PREPARACION = "en_preparacion"
    LISTO = "listo"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(255), nullable=False)
    restaurante_id = db.Column(
        db.Integer, db.ForeignKey("carta_restaurante.id"), nullable=False
    )
    estado = db.Column(db.String(20), nullable=False, default=PENDIENTE)
    fecha = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    restaurante = db.relationship("Restaurante", back_populates="pedidos")
    items = db.relationship("ItemPedido", back_populates="pedido")


class ItemPedido(db.Model):
    __tablename__ = "carta_itempedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer, db.ForeignKey("carta_pedido.id"), nullable=False
    )
    plato_id = db.Column(
        db.Integer, db.ForeignKey("carta_plato.id"), nullable=False
    )
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    pedido = db.relationship("Pedido", back_populates="items")
    plato = db.relationship("Plato", back_populates="items_pedido")


# Perfiles creados mediante las migraciones de Django (carta.0002).
# Auth0 gestiona identidad y permisos; estas tablas solo vinculan personas y restaurantes.
class Usuario(db.Model):
    __tablename__ = "carta_usuario"

    id = db.Column(db.Integer, primary_key=True)
    auth0_sub = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False, default="")
    apellido = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(254), nullable=False, default="")
    telefono = db.Column(db.String(30), nullable=False, default="")

    perfil_empleado = db.relationship("Empleado", back_populates="usuario", uselist=False)


class Empleado(db.Model):
    __tablename__ = "carta_empleado"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("carta_usuario.id"), nullable=False, unique=True)
    restaurante_id = db.Column(db.Integer, db.ForeignKey("carta_restaurante.id"), nullable=True)
    cargo = db.Column(db.String(100), nullable=False)
    fecha_contratacion = db.Column(db.Date, nullable=False, default=date.today)
    activo = db.Column(db.Boolean, nullable=False, default=False)

    usuario = db.relationship("Usuario", back_populates="perfil_empleado")
    restaurante = db.relationship("Restaurante")


class Cliente(db.Model):
    """Tabla creada y migrada por Django, no por Flask."""
    __tablename__ = "carta_cliente"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("carta_usuario.id"), nullable=False, unique=True)
    direccion = db.Column(db.String(255), nullable=False, default="")
    fecha_registro = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    usuario = db.relationship("Usuario", backref=db.backref("perfil_cliente", uselist=False))