from app import create_app, socketio
from app.mqtt_handlers import init_mqtt_handlers
from app.bootstrap import bootstrap

app = create_app()
init_mqtt_handlers(app)
bootstrap(app)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8081, debug=True, use_reloader=False)
