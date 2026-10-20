from flask import Blueprint, jsonify, request
from .extensions import db
from .models import Todo
from .auth import requires_permission
from .auth import requires_auth

bp = Blueprint("api", __name__, url_prefix="/api")

def missing_title():
    return jsonify({"success": False, "error": 400, "code": "missing_title",
                    "message": "Field 'title' is required."}), 400

@bp.get("/todos")
@requires_permission("get:todos")
def list_todos(payload):
    todos = Todo.query.order_by(Todo.completed.asc(), Todo.created_at.desc()).all()
    return jsonify({"success": True, "todos": [t.to_dict() for t in todos]})

@bp.post("/todos")
@requires_permission("post:todos")
def create_todo(payload):
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return missing_title()

    todo = Todo(title=title, description=data.get("description") or None)
    db.session.add(todo)
    db.session.commit()
    return jsonify({"success": True, "todo": todo.to_dict()}), 201

@bp.patch("/todos/<int:todo_id>")
@requires_permission("patch:todos")
def update_todo(payload, todo_id):
    todo = db.get_or_404(Todo, todo_id)
    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return missing_title()
        todo.title = title
    if "description" in data:
        todo.description = data["description"] or None
    if "completed" in data:
        todo.completed = bool(data["completed"])

    db.session.commit()
    return jsonify({"success": True, "todo": todo.to_dict()})

@bp.delete("/todos/<int:todo_id>")
@requires_permission("delete:todos")
def delete_todo(payload, todo_id):
    todo = db.get_or_404(Todo, todo_id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify({"success": True, "deleted": todo_id})

@bp.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": 404, "code": "not_found", "message": "Resource not found."}), 404
