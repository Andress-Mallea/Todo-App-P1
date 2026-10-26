"""CRUD de la carta para el rol admin de Auth0 (R2). Django administra el esquema."""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .auth import requires_auth
from .extensions import db
from .models import Plato, Restaurante

bp = Blueprint('carta_admin', __name__, url_prefix='/administrar')


def _nombre():
    nombre = request.form.get('nombre', '').strip()
    if not 1 <= len(nombre) <= 150:
        abort(400, 'El nombre debe tener entre 1 y 150 caracteres.')
    return nombre


def _precio():
    try:
        precio = Decimal(request.form.get('precio', '').strip())
    except (InvalidOperation, ValueError):
        abort(400, 'El precio debe ser numérico.')
    if not precio.is_finite() or precio < 0 or precio >= Decimal('100000000') or precio.as_tuple().exponent < -2:
        abort(400, 'El precio debe ser no negativo, tener máximo 2 decimales y caber en 10 dígitos.')
    return precio


def _datos_plato():
    nombre = _nombre()
    descripcion = request.form.get('descripcion', '').strip()
    precio = _precio()
    rid = request.form.get('restaurante_id', '').strip()
    try:
        restaurante_id = int(rid)
    except (ValueError, TypeError):
        abort(400, 'Restaurante inválido.')
    db.get_or_404(Restaurante, restaurante_id)
    disponible = request.form.get('disponible') == 'on'
    return dict(nombre=nombre, descripcion=descripcion, precio=precio,
                restaurante_id=restaurante_id, disponible=disponible)


def _guardar():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, 'No se puede completar la operación: existen registros relacionados.')
    except SQLAlchemyError:
        db.session.rollback()
        raise


@bp.get('/')
@requires_auth('write:carta')
def indice(payload):

    restaurantes = (
        Restaurante.query
        .order_by(Restaurante.nombre)
        .all()
    )

    platos = (
        Plato.query
        .order_by(Plato.nombre)
        .all()
    )

    puede_eliminar = 'delete:carta' in payload['permissions']

    # Administrador autenticado mediante JWT local
    if payload["sub"].startswith("local:"):
        return jsonify({
            "restaurantes": [
                {
                    "id": r.id,
                    "nombre": r.nombre,
                    "descripcion": r.descripcion
                }
                for r in restaurantes
            ],
            "platos": [
                {
                    "id": p.id,
                    "nombre": p.nombre,
                    "descripcion": p.descripcion,
                    "precio": str(p.precio),
                    "disponible": p.disponible,
                    "restaurante_id": p.restaurante_id,
                    "restaurante": p.restaurante.nombre
                }
                for p in platos
            ],
            "puede_eliminar": puede_eliminar
        }), 200

    # Administrador autenticado mediante Auth0
    return render_template(
        'carta_admin/index.html',
        restaurantes=restaurantes,
        platos=platos,
        puede_eliminar=puede_eliminar
    )


@bp.route('/restaurantes/nuevo', methods=['GET', 'POST'])
@requires_auth('write:carta')
def nuevo_restaurante(payload):

    if request.method == 'POST':

        restaurante = Restaurante(
            nombre=_nombre(),
            descripcion=request.form.get('descripcion', '').strip()
        )

        db.session.add(restaurante)
        _guardar()

        # JWT local: devolver JSON.
        if payload["sub"].startswith("local:"):
            return jsonify({
                "success": True,
                "message": "Restaurante creado correctamente.",
                "restaurante": {
                    "id": restaurante.id,
                    "nombre": restaurante.nombre,
                    "descripcion": restaurante.descripcion
                }
            }), 201

        # Auth0: conservar el comportamiento original.
        flash('Restaurante creado.', 'success')
        return redirect(
            url_for('carta_admin.indice'),
            code=303
        )

    # Los formularios HTML tradicionales son para Auth0.
    # Evitamos entregar la página de edición a clientes JWT.
    if payload["sub"].startswith("local:"):
        abort(405, "Utiliza el formulario de administración JWT.")

    return render_template(
        'carta_admin/restaurante_form.html',
        restaurante=None
    )


@bp.route('/restaurantes/<int:restaurante_id>/editar', methods=['GET', 'POST'])
@requires_auth('write:carta')
def editar_restaurante(payload, restaurante_id):

    restaurante = db.get_or_404(Restaurante, restaurante_id)

    if request.method == 'POST':
        restaurante.nombre = _nombre()
        restaurante.descripcion = request.form.get(
            'descripcion', ''
        ).strip()

        _guardar()

        # JWT local: respuesta JSON
        if payload["sub"].startswith("local:"):
            return jsonify({
                "success": True,
                "message": "Restaurante actualizado correctamente.",
                "restaurante": {
                    "id": restaurante.id,
                    "nombre": restaurante.nombre,
                    "descripcion": restaurante.descripcion
                }
            }), 200

        # Auth0: conserva su redirección original
        flash('Restaurante actualizado.', 'success')
        return redirect(
            url_for('carta_admin.indice'),
            code=303
        )

    # JWT local: devuelve los datos para un futuro formulario JavaScript
    if payload["sub"].startswith("local:"):
        return jsonify({
            "restaurante": {
                "id": restaurante.id,
                "nombre": restaurante.nombre,
                "descripcion": restaurante.descripcion
            }
        }), 200

    # Auth0: conserva el formulario HTML existente
    return render_template(
        'carta_admin/restaurante_form.html',
        restaurante=restaurante
    )


@bp.post('/restaurantes/<int:restaurante_id>/eliminar')
@requires_auth('delete:carta')
def eliminar_restaurante(payload, restaurante_id):

    restaurante = db.get_or_404(Restaurante, restaurante_id)

    # Impedir eliminar restaurantes que contienen platos.
    if Plato.query.filter_by(restaurante_id=restaurante_id).first():
        abort(409, 'El restaurante tiene platos. No puede eliminarse.')

    # Conservar la información antes de eliminar el registro.
    restaurante_eliminado = {
        "id": restaurante.id,
        "nombre": restaurante.nombre
    }

    db.session.delete(restaurante)
    _guardar()

    # JWT local: respuesta JSON
    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "message": "Restaurante eliminado correctamente.",
            "restaurante": restaurante_eliminado
        }), 200

    # Auth0: comportamiento original
    flash('Restaurante eliminado.', 'success')
    return redirect(
        url_for('carta_admin.indice'),
        code=303
    )


@bp.route('/platos/nuevo', methods=['GET', 'POST'])
@requires_auth('write:carta')
def nuevo_plato(payload):

    if request.method == 'POST':

        # Reutilizamos todas las validaciones existentes.
        datos = _datos_plato()

        plato = Plato(**datos)
        db.session.add(plato)
        _guardar()

        # Administrador JWT local: respuesta JSON.
        if payload["sub"].startswith("local:"):
            return jsonify({
                "success": True,
                "message": "Plato creado correctamente.",
                "plato": {
                    "id": plato.id,
                    "nombre": plato.nombre,
                    "descripcion": plato.descripcion,
                    "precio": str(plato.precio),
                    "disponible": plato.disponible,
                    "restaurante_id": plato.restaurante_id
                }
            }), 201

        # Administrador Auth0: comportamiento original.
        flash('Plato creado.', 'success')
        return redirect(
            url_for('carta_admin.indice'),
            code=303
        )

    # JWT utilizará su propia interfaz JavaScript.
    if payload["sub"].startswith("local:"):
        abort(405, "Utiliza el formulario de administración JWT.")

    # Auth0 conserva el formulario HTML existente.
    return render_template(
        'carta_admin/plato_form.html',
        plato=None,
        restaurantes=Restaurante.query.order_by(
            Restaurante.nombre
        ).all()
    )

@bp.route('/platos/<int:plato_id>/editar', methods=['GET', 'POST'])
@requires_auth('write:carta')
def editar_plato(payload, plato_id):

    plato = db.get_or_404(Plato, plato_id)

    if request.method == 'POST':
        # Reutilizamos las validaciones existentes.
        datos = _datos_plato()

        for campo, valor in datos.items():
            setattr(plato, campo, valor)

        _guardar()

        # JWT local: respuesta JSON.
        if payload["sub"].startswith("local:"):
            return jsonify({
                "success": True,
                "message": "Plato actualizado correctamente.",
                "plato": {
                    "id": plato.id,
                    "nombre": plato.nombre,
                    "descripcion": plato.descripcion,
                    "precio": str(plato.precio),
                    "disponible": plato.disponible,
                    "restaurante_id": plato.restaurante_id
                }
            }), 200

        # Auth0: comportamiento original.
        flash('Plato actualizado.', 'success')
        return redirect(
            url_for('carta_admin.indice'),
            code=303
        )

    # JWT local: datos para la interfaz JavaScript.
    if payload["sub"].startswith("local:"):
        return jsonify({
            "plato": {
                "id": plato.id,
                "nombre": plato.nombre,
                "descripcion": plato.descripcion,
                "precio": str(plato.precio),
                "disponible": plato.disponible,
                "restaurante_id": plato.restaurante_id
            }
        }), 200

    # Auth0: conserva el formulario HTML.
    return render_template(
        'carta_admin/plato_form.html',
        plato=plato,
        restaurantes=Restaurante.query.order_by(
            Restaurante.nombre
        ).all()
    )

@bp.post('/platos/<int:plato_id>/eliminar')
@requires_auth('delete:carta')
def eliminar_plato(payload, plato_id):

    plato = db.get_or_404(Plato, plato_id)

    # Guardamos estos datos antes de eliminar el registro.
    plato_eliminado = {
        "id": plato.id,
        "nombre": plato.nombre
    }

    db.session.delete(plato)

    # Conservamos la validación de integridad existente.
    # PostgreSQL impide eliminar platos utilizados en pedidos.
    _guardar()

    # JWT local: respuesta JSON.
    if payload["sub"].startswith("local:"):
        return jsonify({
            "success": True,
            "message": "Plato eliminado correctamente.",
            "plato": plato_eliminado
        }), 200

    # Auth0: conserva su comportamiento original.
    flash("Plato eliminado.", "success")
    return redirect(
        url_for("carta_admin.indice"),
        code=303
    )
@bp.get('/local')
def panel_local():
        # Solo entrega la interfaz HTML.
        # Los datos y las operaciones se protegen con JWT
        # en las rutas administrativas existentes.
    return render_template('carta_admin/index_local.html')