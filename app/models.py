"""Modelos SQLAlchemy sobre tablas administradas exclusivamente por Django.

No ejecutar db.create_all() ni Flask-Migrate sobre estas tablas en producción.
"""
from datetime import datetime, timezone

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