from urllib.parse import urlencode

from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, current_app, flash, redirect, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Cliente, Empleado, Usuario
from .oauth import auth0
from .tokens import verify_decode_jwt
from .errors import AuthError

bp = Blueprint("auth", __name__, url_prefix="/auth")


def safe_next(target):
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("carta.restaurantes")


@bp.get("/login")
def login():
    session["next"] = safe_next(request.args.get("next"))
    return auth0().authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True),
        audience=current_app.config["AUTH0_AUDIENCE"],
    )


@bp.get("/callback")
def callback():
    try:
        token = auth0().authorize_access_token()
    except OAuthError as err:
        flash(f"No se completó el login: {err.description or err.error}", "error")
        return redirect(url_for("carta.restaurantes"))

    # Nunca confiar en un 'sub' o en permisos suministrados por el navegador.
    # Validamos el access token con el mismo verificador de las rutas protegidas.
    try:
        payload = verify_decode_jwt(token["access_token"])
    except AuthError as err:
        current_app.logger.warning(
            "Error verificando token Auth0: codigo=%s, descripcion=%s",
            err.error.get("code"),
            err.error.get("description"),
        )

        session.clear()

        flash(
            "No se pudo verificar el acceso. Intenta iniciar sesión nuevamente.",
            "error"
        )

        return redirect(url_for("carta.restaurantes"))

    except KeyError:
        current_app.logger.warning(
            "La respuesta de Auth0 no contiene access_token"
        )

        session.clear()

        flash(
            "No se pudo verificar el acceso. Intenta iniciar sesión nuevamente.",
            "error"
        )

        return redirect(url_for("carta.restaurantes"))

    profile = token.get("userinfo") or {}
    auth0_sub = payload["sub"]
    permisos = payload.get("permissions") or []
    # La aplicación Auth0 asigna permisos, no relaciones comerciales.
    # Damos prioridad al personal, incluso si el token trae permisos de cliente.
    permisos = set(permisos)
    es_admin = bool(permisos & {"write:carta", "delete:carta"})
    es_cocina = bool(permisos & {"update:pedidos", "read:pedidos"})
    es_personal = es_admin or es_cocina
    es_cliente = not es_personal and {"create:pedidos", "read:mis-pedidos"}.issubset(permisos)

    nombre_completo = (profile.get("name") or "").strip()
    nombre = (profile.get("given_name") or nombre_completo).strip()[:120]
    apellido = (profile.get("family_name") or "").strip()[:120]
    email = (profile.get("email") or "").strip()[:254]

    try:
        usuario = Usuario.query.filter_by(auth0_sub=auth0_sub).first()
        if usuario is None:
            usuario = Usuario(auth0_sub=auth0_sub, nombre=nombre, apellido=apellido, email=email)
            db.session.add(usuario)
            db.session.flush()
        else:
            # Mantener los datos registrados en Django cuando Auth0 omita campos.
            if nombre:
                usuario.nombre = nombre
            if apellido:
                usuario.apellido = apellido
            if email:
                usuario.email = email

        empleado_existente = Empleado.query.filter_by(usuario_id=usuario.id).first()
        if es_personal:
            if empleado_existente is None:
                db.session.add(Empleado(
                    usuario_id=usuario.id,
                    restaurante_id=None,
                    cargo="Administrador" if es_admin else "Cocina",
                    activo=False,
                ))
            # No modificar la asignación de empleados existentes.
            # No borrar perfiles Cliente antiguos: podrían tener datos relacionados.
        elif es_cliente and empleado_existente is None:
            if Cliente.query.filter_by(usuario_id=usuario.id).first() is None:
                db.session.add(Cliente(usuario_id=usuario.id, direccion=""))

        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("No se pudo sincronizar el perfil de Auth0")
        session.clear()
        flash("No se pudo guardar el perfil. Intenta iniciar sesión nuevamente.", "error")
        return redirect(url_for("carta.restaurantes"))

    next_url = session.pop("next", None) or url_for("carta.restaurantes")
    session.clear()
    session["access_token"] = token["access_token"]
    session["user"] = {"name": profile.get("name") or email or auth0_sub, "email": email}
    return redirect(next_url)


@bp.post("/logout")
def logout():
    session.clear()
    params = urlencode({
        "returnTo": url_for("carta.restaurantes", _external=True),
        "client_id": current_app.config["AUTH0_CLIENT_ID"],
    })
    return redirect(f"https://{current_app.config['AUTH0_DOMAIN']}/v2/logout?{params}")