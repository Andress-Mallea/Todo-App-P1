from flask import Flask, session
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    for key in ("AUTH0_DOMAIN", "AUTH0_AUDIENCE", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET"):
        if not app.config[key]:
            raise RuntimeError(f"Falta {key} en el entorno del contenedor Flask")

    if app.config.get("BEHIND_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    from . import models  # noqa: F401
    from .auth import AuthError, jwks_client
    from .auth.handlers import handle_auth_error
    from .auth.oauth import init_auth0
    from .auth.routes import bp as auth_bp
    from .auth.decorators import current_user
    from .routes import bp as root_bp
    from .carta_routes import bp as carta_bp
    from .carta_admin_routes import bp as carta_admin_bp

    init_auth0(app)
    app.extensions["auth0_jwks"] = jwks_client(app.config["AUTH0_DOMAIN"])
    for bp in (auth_bp, root_bp, carta_bp, carta_admin_bp):
        app.register_blueprint(bp)
    app.register_error_handler(AuthError, handle_auth_error)

    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    return app
