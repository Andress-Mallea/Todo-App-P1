from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import text
from .auth import requires_bearer_auth

from .extensions import db

bp = Blueprint("restaurant", __name__)

# Lista blanca: tabla -> ORDER BY (nunca se usa texto del usuario en el SQL)
ORDER_BY = {
    "category": "name",
    "product": "name",
    "customer": "email",
    "dining_table": "table_number",
    "customer_order": "created_at DESC, id",
    "order_line": "id",
    "promotion": "name",
    "promotion_product": "id",
}


def clean(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="seconds")
    return str(value)


@bp.get("/restaurant")
def page():
    return render_template("restaurant.html")


@bp.get("/api/restaurant/<table>")
@requires_bearer_auth("get:restaurant")
def table_rows(payload, table):
    order = ORDER_BY.get(table)
    if order is None:
        return jsonify({"success": False, "error": 404, "code": "unknown_table",
                        "message": "Unknown table."}), 404

    page_num = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 50, type=int), 1), 200)

    total = db.session.execute(text(f"SELECT count(*) FROM content.{table}")).scalar()
    result = db.session.execute(
        text(f"SELECT * FROM content.{table} ORDER BY {order} LIMIT :limit OFFSET :offset"),
        {"limit": per_page, "offset": (page_num - 1) * per_page},
    )
    columns = list(result.keys())
    rows = [[clean(v) for v in row] for row in result]

    return jsonify({
        "success": True,
        "table": table,
        "columns": columns,
        "rows": rows,
        "total": total,
        "page": page_num,
        "pages": max((total + per_page - 1) // per_page, 1),
    })