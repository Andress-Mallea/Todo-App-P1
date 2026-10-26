import re

from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import CuentaLocal
from .local_tokens import create_local_access_token

bp = Blueprint("local_auth", __name__, url_prefix="/auth/local")
@bp.get("/entrar")
def pagina_login_local():
    return render_template("auth/login_unificado.html")
USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,80}$")

# Evita diferencias evidentes en el tiempo de respuesta cuando
# un usuario no existe.
DUMMY_HASH = generate_password_hash("dummy-password")


def obtener_credenciales():
    datos = request.get_json(silent=True) or {}

    if not isinstance(datos, dict):
        return "", ""

    username = datos.get("username", "")
    password = datos.get("password", "")

    if not isinstance(username, str) or not isinstance(password, str):
        return "", ""

    return username.strip().lower(), password


@bp.post("/register")
def registrar():
    username, password = obtener_credenciales()

    if not USERNAME_RE.fullmatch(username):
        return jsonify(
            success=False,
            message="El usuario debe tener entre 3 y 80 caracteres válidos."
        ), 400

    if len(password) < 8:
        return jsonify(
            success=False,
            message="La contraseña debe tener al menos 8 caracteres."
        ), 400

    if CuentaLocal.query.filter_by(username=username).first():
        return jsonify(
            success=False,
            message="El usuario ya está registrado."
        ), 409

    usuario = CuentaLocal(username=username)
    usuario.set_password(password)

    try:
        db.session.add(usuario)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(
            success=False,
            message="El usuario ya está registrado."
        ), 409

    return jsonify(
        success=True,
        message="Usuario registrado correctamente.",
        user={
            "id": usuario.id,
            "username": usuario.username
        }
    ), 201


@bp.post("/login")
def iniciar_sesion():
    username, password = obtener_credenciales()

    usuario = CuentaLocal.query.filter_by(username=username).first()

    if usuario is None:
        check_password_hash(DUMMY_HASH, password)
        valido = False
    else:
        valido = usuario.check_password(password)

    if not valido:
        return jsonify(
            success=False,
            message="Usuario o contraseña incorrectos."
        ), 401

    token = create_local_access_token(usuario)

    return jsonify(
        success=True,
        access_token=token,
        token_type="Bearer",
        expires_in=current_app.config["LOCAL_JWT_EXPIRES_MINUTES"] * 60
    ), 200