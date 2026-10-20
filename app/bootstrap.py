from werkzeug.security import generate_password_hash
from app.models.user import User, Role
from app.controllers.sensors import ensure_default_sensors, initialize_sensors
from app.controllers.actuators import ensure_servo_actuator
from app.extensions import db

def bootstrap(app):
    with app.app_context():
        db.create_all()

        for name in ("Admin", "User"):
            if not Role.query.filter_by(name=name).first():
                db.session.add(Role(name=name))
        db.session.commit()

        role_admin = Role.query.filter_by(name="Admin").first()

        defaults = [
            ("admin", "admin@gmail.com", "admin", role_admin, "admin"),
            ("operador", "operador@gmail.com", "operador", role_admin, "operator"),
            ("estatistico", "estatistico@gmail.com", "estatistico", role_admin, "estatistico"),
        ]
        for uname, email, pwd, role, function in defaults:
            if not User.query.filter_by(username=uname).first():
                db.session.add(User(
                    username=uname,
                    email=email,
                    password=generate_password_hash(pwd),
                    role=role,
                    function=function,
                ))
        db.session.commit()

        ensure_servo_actuator()
        ensure_default_sensors()
        initialize_sensors(app)
