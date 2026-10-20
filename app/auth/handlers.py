from flask import jsonify
from .errors import AuthError

def handle_auth_error(err: AuthError):
    """Every auth failure becomes the same JSON shape, with its real status code."""
    return jsonify({
        "success": False,
        "error": err.status_code,
        "code": err.error["code"],
        "message": err.error["description"],
    }), err.status_code