import jwt
from flask import current_app

from .errors import AuthError

ALGORITHMS = ["RS256"]


def jwks_client(domain):
    """Descarga las claves públicas una vez y las guarda en memoria."""
    return jwt.PyJWKClient(f"https://{domain}/.well-known/jwks.json", cache_keys=True, timeout=5)


def verify_decode_jwt(token):
    """Devuelve el payload de un token válido de Auth0 o lanza AuthError."""
    domain = current_app.config["AUTH0_DOMAIN"]
    try:
        signing_key = current_app.extensions["auth0_jwks"].get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,
            audience=current_app.config["AUTH0_AUDIENCE"],
            issuer=f"https://{domain}/",
            options={"require": ["exp", "iat", "sub"]},
            leeway=30,
        )
    except jwt.ExpiredSignatureError:
        raise AuthError({"code": "token_expired", "description": "Token expired."}, 401)
    except (jwt.InvalidAudienceError, jwt.InvalidIssuerError):
        raise AuthError({"code": "invalid_claims",
                         "description": "Incorrect claims. Please, check the audience and issuer."}, 401)
    except jwt.PyJWKClientConnectionError:
        raise AuthError({"code": "jwks_unavailable", "description": "Unable to fetch the signing keys."}, 503)
    except jwt.PyJWKClientError:
        raise AuthError({"code": "invalid_header", "description": "Unable to find the appropriate key."}, 401)
    except jwt.InvalidTokenError as err:
        current_app.logger.warning(
            "Auth0 JWT rechazado: tipo=%s",
            type(err).__name__
        )

        raise AuthError(
            {
                "code": "invalid_token",
                "description": "Invalid token."
            },
            401
        ) from err