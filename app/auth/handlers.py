from flask import jsonify, render_template, request, session
from .errors import AuthError


def handle_auth_error(err):
    if request.path.startswith("/api/"):
        return jsonify(success=False, error=err.status_code, code=err.error["code"],
                       message=err.error["description"]), err.status_code
    if err.status_code == 401:
        session.pop("access_token", None)
        return render_template("auth/signin.html", next=request.path), 401
    return render_template("auth/forbidden.html", status=err.status_code,
                           message=err.error["description"]), err.status_code