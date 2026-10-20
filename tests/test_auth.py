import base64
import json
import jwt
import pytest
from app.extensions import db
from app.models import Todo, User
from tests.conftest import PASSWORD
def bearer(token):
    return {"Authorization": f"Bearer {token}"}
# ---------------------------------------------------------------- register
def test_register_creates_a_user_and_rejects_duplicates(client):
    ok = client.post("/auth/register", json={"username": "nuevo", "password": "una-clavelarga"})
    assert ok.status_code == 201
    assert ok.get_json()["user"]["username"] == "nuevo"
    dup = client.post("/auth/register", json={"username": "nuevo", "password": "una-clavelarga"})
    assert dup.status_code == 409
@pytest.mark.parametrize("username, password, code", [
    ("ab", "una-clave-larga", "invalid_username"),
    ("con espacios", "una-clave-larga", "invalid_username"),
    ("valido", "corta", "weak_password"),
    ])
def test_register_validates_the_input(client, username, password, code):
    res = client.post("/auth/register", json={"username": username, "password": password})
    assert res.status_code == 400
    assert res.get_json()["code"] == code
def test_passwords_are_stored_hashed(app):
    user = User.query.filter_by(username="ana").first()
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("scrypt:")
def test_a_new_user_can_log_in(client):
    client.post("/auth/register", json={"username": "nuevo", "password": "una-clave-larga"})
    res = client.post("/auth/login", json={"username": "nuevo", "password": "una-clave-larga"})
    assert res.status_code == 200
    assert res.get_json()["token_type"] == "Bearer"
# ---------------------------------------------------------------- login
def test_login_returns_a_signed_jwt(app, token):
    payload = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"],
    issuer=app.config["JWT_ISSUER"])
    assert payload["username"] == "ana"
    assert payload["exp"] > payload["iat"]
def test_login_sets_no_cookie(client):
    res = client.post("/auth/login", json={"username": "ana", "password": PASSWORD})
    assert res.status_code == 200
    assert "Set-Cookie" not in res.headers
@pytest.mark.parametrize("username, password", [("ana", "wrong-password"), ("nobody",
PASSWORD)])
def test_bad_credentials_get_the_same_401(client, username, password):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 401
    assert res.get_json()["message"] == "Invalid username or password."
    # ---------------------------------------------------------------- the two filters
@pytest.mark.parametrize("header, code", [
    (None, "authorization_header_missing"),
    (" ", "authorization_header_missing"),
    ("Token abc", "invalid_header"),
    ("Bearer", "invalid_header"),
    ("Bearer a b", "invalid_header"),
    ("Bearer not.a.token", "invalid_token"),
    ])
def test_no_valid_token_no_access(client, header, code):
    headers = {} if header is None else {"Authorization": header}
    res = client.get("/api/todos", headers=headers)
    assert res.status_code == 401
    assert res.get_json()["code"] == code
def test_a_token_in_a_cookie_is_ignored(client, token):
    """Only the Authorization header counts: the browser cannot send it by itself."""
    client.set_cookie("access_token", token)
    res = client.get("/api/todos")
    assert res.status_code == 401
    assert res.get_json()["code"] == "authorization_header_missing"
def test_expired_token_is_rejected(app, client):
    app.config["JWT_EXPIRES_MINUTES"] = -1
    res = client.post("/auth/login", json={"username": "ana", "password": PASSWORD})
    expired = res.get_json()["access_token"]
    res = client.get("/api/todos", headers=bearer(expired))
    assert res.status_code == 401
    assert res.get_json()["code"] == "token_expired"
def test_tampered_payload_is_rejected(client, token):
    header, payload, signature = token.split(".")
    data = json.loads(base64.urlsafe_b64decode(payload + "=="))
    data["sub"] = "999" # try to become someone else
    forged = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    res = client.get("/api/todos", headers=bearer(f"{header}.{forged}.{signature}"))
    assert res.status_code == 401
def test_alg_none_token_is_rejected(client):
    unsigned = jwt.encode({"sub": "1", "username": "ana"}, key=None, algorithm="none")
    res = client.get("/api/todos", headers=bearer(unsigned))
    assert res.status_code == 401
# ---------------------------------------------------------------- API
def test_api_create_and_list(client, token):
    res = client.post("/api/todos", json={"title": "Desde la API"}, headers=bearer(token))
    assert res.status_code == 201
    titles = [t["title"] for t in client.get("/api/todos", headers=bearer(token)).get_json()
    ["todos"]]
    assert "Desde la API" in titles
def test_api_patch_toggles_and_renames(client, token):
    res = client.patch("/api/todos/1", json={"completed": True, "title": "Renombrada"},
    headers=bearer(token))
    assert res.status_code == 200
    todo = res.get_json()["todo"]
    assert todo["completed"] is True
    assert todo["title"] == "Renombrada"
def test_api_delete(client, token):
    res = client.delete("/api/todos/1", headers=bearer(token))
    assert res.status_code == 200
    assert db.session.get(Todo, 1) is None
def test_api_missing_todo_is_a_json_404(client, token):
    res = client.delete("/api/todos/999", headers=bearer(token))
    assert res.status_code == 404
    assert res.get_json()["code"] == "not_found"
# ---------------------------------------------------------------- page
def test_page_is_a_public_shell_without_data(client):
    """The HTML carries no todos: they only come from the protected API."""
    res = client.get("/")
    assert res.status_code == 200
    page = res.get_data(as_text=True)
    assert "login-form" in page
    assert "Primera tarea" not in page