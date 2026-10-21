from authlib.integrations.flask_client import OAuth
from flask import current_app


def init_auth0(app):
    oauth = OAuth(app)
    oauth.register(
        name="auth0",
        client_id=app.config["AUTH0_CLIENT_ID"],
        client_secret=app.config["AUTH0_CLIENT_SECRET"],
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f"https://{app.config['AUTH0_DOMAIN']}/.well-known/openid-configuration",
    )


def auth0():
    return current_app.extensions["authlib.integrations.flask_client"].auth0
