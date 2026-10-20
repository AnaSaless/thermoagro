from app.extensions import db
from flask_login import UserMixin

class Role(db.Model):
    __tablename__ = "roles"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"<Role {self.name}>"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role_id  = db.Column(db.Integer, db.ForeignKey("roles.id"))
    role     = db.relationship("Role", backref="users")

    function = db.Column(db.String(20), default="user")

    @property
    def is_admin(self):
        return self.role and self.role.name == "Admin"

    @property
    def is_operator(self):
        return self.function == "operator"

    @property
    def is_estatistico(self):
        return self.function == "estatistico"
