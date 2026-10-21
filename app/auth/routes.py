from urllib.parse import urlencode
from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, current_app, flash, redirect, request, session, url_for
from .oauth import auth0

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
    next_url = session.pop("next", None) or url_for("carta.restaurantes")
    profile = token.get("userinfo") or {}
    session.clear()
    session["access_token"] = token["access_token"]
    session["user"] = {"name": profile.get("name") or profile.get("email"), "email": profile.get("email")}
    return redirect(next_url)

@bp.post("/logout")
def logout():
    session.clear()
    params = urlencode({"returnTo": url_for("carta.restaurantes", _external=True),
                       "client_id": current_app.config["AUTH0_CLIENT_ID"]})
    return redirect(f"https://{current_app.config['AUTH0_DOMAIN']}/v2/logout?{params}")
