from flask import Flask
from flask_socketio import SocketIO
from flask_mqtt import Mqtt
from app.models.user import User
import os

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
mqtt = Mqtt()
mqtt_ok = {"connected": False}

def create_app():
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'views', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.secret_key = "banana"

    socketio.init_app(app)

    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MQTT_BROKER_URL="broker.emqx.io",
        MQTT_BROKER_PORT=1883,
        MQTT_KEEPALIVE=60,
        MQTT_TLS_ENABLED=False,
        SERVO_ANGLE=90,
        WOKWI_URL=""
    )

    from .extensions import db, migrate, login_manager
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    mqtt.init_app(app)

    from app.controllers import auth, sensors, actuators, user
    app.register_blueprint(auth.bp)
    app.register_blueprint(sensors.bp)
    app.register_blueprint(actuators.bp)
    app.register_blueprint(user.user)  

    from flask_login import current_user
    from app.controllers.sensors import sensors
    from app.controllers.actuators import get_actuators_dict

    @app.context_processor
    def inject_globals():
        return dict(
            sensors=sensors,
            actuators=get_actuators_dict(),
            current_user=current_user,
        )

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
