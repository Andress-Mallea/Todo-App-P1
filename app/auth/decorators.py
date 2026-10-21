from functools import wraps

from flask import request

from .errors import AuthError
from .tokens import verify_decode_jwt


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
    """Para las páginas Flask: 401 sin sesión, 403 sin permiso."""
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            payload = verify_decode_jwt(get_token_from_session())
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
