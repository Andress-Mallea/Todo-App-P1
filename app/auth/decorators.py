from functools import wraps

from flask import request

from .errors import AuthError
from .tokens import verify_decode_jwt
from .local_tokens import verify_local_jwt
from app.models import CuentaLocal
from app.extensions import db
PERMISOS_POR_ROL = {
    "cliente": [
        "create:pedidos",
        "read:mis-pedidos",
    ],
    "cocina": [
        "read:pedidos",
        "update:pedidos",
    ],
    "admin": [
        "read:pedidos",
        "write:carta",
        "delete:carta",
    ],
}
def get_token_auth_header():
    """Devuelve el JWT de 'Authorization: Bearer <token>'."""
    auth = request.headers.get("Authorization", "").strip()
    if not auth:
        raise AuthError({"code": "authorization_header_missing", "description": "Authorization header is expected."}, 401)

    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header", "description": 'Authorization header must start with "Bearer".'}, 401)
    if len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found."}, 401)
    if len(parts) > 2:
        raise AuthError({"code": "invalid_header", "description": 'Authorization header must be "Bearer <token>".'}, 401)

    return parts[1]


def check_permissions(permission, payload):
    if "permissions" not in payload:
        raise AuthError({"code": "invalid_claims", "description": "Permissions not included in the token."}, 400)
    if permission and permission not in payload["permissions"]:
        raise AuthError({"code": "forbidden", "description": "You do not have permission to perform this action."}, 403)
    return True


def get_token_from_session():
    from flask import session
    token = session.get("access_token")
    if not token:
        raise AuthError({"code": "not_signed_in", "description": "Inicia sesión para continuar."}, 401)
    return token


def requires_auth(permission=""):
    """
    Permite dos mecanismos:
    - JWT local HS256 desde Authorization: Bearer
    - Auth0 RS256 desde la sesión Flask existente
    """

    def decorator(fn):

        @wraps(fn)
        def wrapped(*args, **kwargs):

            authorization = request.headers.get(
                "Authorization", ""
            ).strip()

            if authorization:
               
                token = get_token_auth_header()
                payload = verify_local_jwt(token)

                sub = payload.get("sub", "")

                if not isinstance(sub, str) or not sub.startswith("local:"):
                    raise AuthError({
                        "code": "invalid_token",
                        "description": "Identidad JWT local inválida."
                    }, 401)

                try:
                    usuario_id = int(sub.removeprefix("local:"))
                except ValueError:
                    raise AuthError({
                        "code": "invalid_token",
                        "description": "Identidad JWT local inválida."
                    }, 401)

                usuario = db.session.get(CuentaLocal, usuario_id)

                if usuario is None:
                    raise AuthError({
                        "code": "invalid_token",
                        "description": "La cuenta ya no existe."
                    }, 401)

                rol = usuario.rol

                payload["permissions"] = PERMISOS_POR_ROL.get(rol, [])

            else:
               
                payload = verify_decode_jwt(
                    get_token_from_session()
                )

            check_permissions(permission, payload)

            return fn(payload, *args, **kwargs)

        return wrapped

    return decorator


def requires_bearer_auth(permission=""):
    """Se conserva solo para las rutas JSON antiguas; no es el login de La Carta."""
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            payload = verify_decode_jwt(get_token_auth_header())
            check_permissions(permission, payload)
            return fn(payload, *args, **kwargs)
        return wrapped
    return decorator


def current_user():
    from flask import session
    token = session.get("access_token")
    if not token:
        return None
    try:
        payload = verify_decode_jwt(token)
    except AuthError:
        return None
    profile = session.get("user", {})
    return {"name": profile.get("name") or profile.get("email") or payload["sub"],
            "sub": payload["sub"], "permissions": payload.get("permissions", [])}
