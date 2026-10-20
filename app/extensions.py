from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_mqtt import Mqtt

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
mqtt = Mqtt()
