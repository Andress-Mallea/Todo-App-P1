from app import create_app
from app.extensions import db
from app.models import User


def crear_usuarios_por_defecto():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('123')
            db.session.add(admin)
            print("Usuario 'admin' creado automáticamente.")
        else:
            admin.role = 'admin'

        visitante = User.query.filter_by(username='visitante').first()
        if not visitante:
            visitante = User(username='visitante', role='user')
            visitante.set_password('123')
            db.session.add(visitante)
            print("Usuario 'visitante' creado automáticamente.")

        db.session.commit()


if __name__ == '__main__':
    crear_usuarios_por_defecto()