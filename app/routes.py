from flask import Blueprint, render_template

bp = Blueprint("todos", __name__)

@bp.route("/")
def index():
    """
    La página es un cascarón público sin datos.
    Su JavaScript inicia sesión mediante /auth/login y carga las tareas
    desde /api/todos enviando el header Bearer.
    """
    return render_template("index.html")