import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql+psycopg2://app:123qwe@db:5432/movies_database' # <-- Cambio aquí
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
# 1. Modelo de la Base de Datos
class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

# 2. Rutas de la Aplicación
@app.route('/', methods=['GET'])
def index():
    # Ordena las tareas mostrando las más recientes primero
    todos = Todo.query.order_by(Todo.completed.asc(), Todo.created_at.desc()).all()
    return render_template('index.html', todos=todos)

@app.route('/todos', methods=['POST'])
def create():
    title = request.form.get("title", "").strip()
    if title:
        nuevo_todo = Todo(title=title)
        db.session.add(nuevo_todo)
        db.session.commit()
    # Redirección obligatoria después de un POST exitoso
    return redirect(url_for('index'))

@app.route('/todos/<int:todo_id>/delete', methods=['POST'])
def delete(todo_id):
    todo = Todo.query.get(todo_id)
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        app.run(host='0.0.0.0', port=8000)