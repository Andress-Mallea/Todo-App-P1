from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from .errors import AuthError


LOCAL_ALGORITHM = "HS256"


def create_local_access_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": f"local:{user.id}",
        "username": user.username,
        "iat": now,
        "exp": now + timedelta(
            minutes=current_app.config["LOCAL_JWT_EXPIRES_MINUTES"]
        ),
        "iss": current_app.config["LOCAL_JWT_ISSUER"],
    }

    return jwt.encode(
        payload,
        current_app.config["LOCAL_JWT_SECRET_KEY"],
        algorithm=LOCAL_ALGORITHM,
    )


def verify_local_jwt(token):
    try:
        return jwt.decode(
            token,
            current_app.config["LOCAL_JWT_SECRET_KEY"],
            algorithms=[LOCAL_ALGORITHM],
            issuer=current_app.config["LOCAL_JWT_ISSUER"],
            options={"require": ["exp", "iat", "sub", "iss"]},
        )

    except jwt.ExpiredSignatureError:
        raise AuthError(
            {
                "code": "token_expired",
                "description": "El token JWT ha expirado.",
            },
            401,
        )

    except jwt.InvalidTokenError:
        raise AuthError(
            {
                "code": "invalid_token",
                "description": "El token JWT no es válido.",
            },
            401,
        )