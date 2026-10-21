from flask import Blueprint, redirect, url_for

bp = Blueprint("todos", __name__)

@bp.get("/")
def index():
    return redirect(url_for("carta.restaurantes"))