from app import app, db
from models.user import User, Role

with app.app_context():
    db.create_all()
    print("Banco de dados criado!")
