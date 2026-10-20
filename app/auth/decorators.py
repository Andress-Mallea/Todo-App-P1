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


def requires_auth(permission=""):
    """Uso: @requires_auth('delete:todos'). Filtros: token (401), válido (401), permiso (403)."""
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            payload = verify_decode_jwt(get_token_auth_header())
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator