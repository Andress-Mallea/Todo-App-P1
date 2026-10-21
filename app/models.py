from datetime import datetime, timezone
from .extensions import db

def utcnow():
    return datetime.now(timezone.utc)

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