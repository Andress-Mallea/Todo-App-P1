"""Auth0: verificación de tokens RS256 y decorador de permisos."""

from .decorators import check_permissions, get_token_auth_header, requires_auth
from .errors import AuthError
from .tokens import jwks_client, verify_decode_jwt

__all__ = [
    "AuthError",
    "check_permissions",
    "get_token_auth_header",
    "jwks_client",
    "requires_auth",
    "verify_decode_jwt",
]