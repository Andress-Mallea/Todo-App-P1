from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    role = db.Column(db.String(20), nullable=False, default="user", server_default="user")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def verify_hash(password_hash, password):
        return check_password_hash(password_hash, password)

    def __repr__(self):
        return f"<User {self.id} {self.username!r}>"

class Todo(db.Model):
    __tablename__ = "todos"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Todo {self.id} {self.title!r} completed={self.completed}>"