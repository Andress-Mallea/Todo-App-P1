from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    for key in ("AUTH0_DOMAIN", "AUTH0_AUDIENCE", "AUTH0_CLIENT_ID"):
        if not app.config[key]:
            raise RuntimeError(f"{key} is not set. Define it in .env or docker-compose.yml.")

    db.init_app(app)

    from . import models  # noqa: F401

    from .api import bp as api_bp
    from .auth import AuthError, jwks_client
    from .auth.handlers import handle_auth_error
    from .restaurant import bp as restaurant_bp
    from .routes import bp as todos_bp

    # Un cliente de claves por app, para que su caché dure lo que el proceso
    app.extensions["auth0_jwks"] = jwks_client(app.config["AUTH0_DOMAIN"])

    app.register_blueprint(todos_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(restaurant_bp)
    app.register_error_handler(AuthError, handle_auth_error)

    @app.context_processor
    def inject_auth0():
        # Estos tres datos no son secretos: el navegador los necesita para armar el login
        return {"auth0_config": {
            "domain": app.config["AUTH0_DOMAIN"],
            "clientId": app.config["AUTH0_CLIENT_ID"],
            "audience": app.config["AUTH0_AUDIENCE"],
        }}

    return app