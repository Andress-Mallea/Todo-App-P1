import re
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models import User
from .tokens import create_access_token

bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,80}$")
MIN_PASSWORD = 8

# Para mitigar el descubrimiento de usuarios, cuando no existe un usuario tardamos lo mismo
_DUMMY_HASH = generate_password_hash("not-a-real-password")

def json_error(status, code, message):
    return jsonify({"success": False, "error": status, "code": code, "message": message}), status

def read_credentials():
    data = request.get_json(silent=True) or {}
    return str(data.get("username", "")).strip().lower(), str(data.get("password", ""))

def authenticate(username, password):
    """Return the User if the credentials are valid, otherwise None."""
    user = User.query.filter_by(username=username).first()
    if user is None:
        User.verify_hash(_DUMMY_HASH, password)
        return None
    return user if user.check_password(password) else None

@bp.post("/register")
def register():
    username, password = read_credentials()
    
    if not USERNAME_RE.match(username):
        return json_error(400, "invalid_username", "Username: 3-80 characters, lowercase letters, numbers, dot, dash or underscore.")
    if len(password) < MIN_PASSWORD:
        return json_error(400, "weak_password", f"Password must be at least {MIN_PASSWORD} characters.")
    if User.query.filter_by(username=username).first():
        return json_error(409, "username_taken", "That username is taken.")

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"success": True, "user": {"id": user.id, "username": user.username}}), 201

@bp.post("/login")
def login():
    """JSON credentials in, signed JWT out. The client keeps the token."""
    user = authenticate(*read_credentials())
    if user is None:
        return json_error(401, "invalid_credentials", "Invalid username or password.")
        
    return jsonify({
        "access_token": create_access_token(user),
        "token_type": "Bearer",
        "expires_in": current_app.config["JWT_EXPIRES_MINUTES"] * 60,
    })