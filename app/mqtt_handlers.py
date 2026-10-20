import json
from datetime import datetime, timezone
from flask_socketio import SocketIO
from flask_mqtt import Mqtt
from app.extensions import db
from app.models.sensor_reading import SensorReading
from app.controllers.sensors import sensors

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
mqtt = Mqtt()
mqtt_ok = {"connected": False}

def init_mqtt_handlers(app):
    mqtt.init_app(app)
    socketio.init_app(app)

    @mqtt.on_connect()
    def mqtt_connected(_, __, ___, rc):
        if rc == 0:
            mqtt_ok["connected"] = True
            unique_topics = {s['topic'] for s in sensors.values()}
            for t in unique_topics:
                mqtt.subscribe(t)
            print("✅ MQTT conectado – tópicos:", ", ".join(unique_topics))
        else:
            print("❌ Falha MQTT:", rc)

    @mqtt.on_disconnect()
    def mqtt_disc(*_):
        mqtt_ok["connected"] = False
        print("🔌 MQTT desconectado")

    @mqtt.on_message()
    def handle_mqtt_message(_, __, msg):
        if msg.topic != 'sensor':
            return

        try:
            payload = json.loads(msg.payload.decode())
            sensor_id = int(payload['id'])
            value = float(payload['value'])
        except (KeyError, ValueError, json.JSONDecodeError):
            return

        for key, cfg in sensors.items():
            if cfg['id'] == sensor_id:
                cfg['value'] = value
                cfg['color'] = cfg['assess'](value, cfg['defaults'])
                socketio.emit('sensor_update', {
                    'sensor': key, 'value': value, 'color': cfg['color']
                })
                cfg['history'].append({
                    'ts': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S'),
                    'value': value,
                    'color': cfg['color'],
                })

                with app.app_context():
                    db.session.add(SensorReading(
                        sensor_id=sensor_id,
                        value=value,
                        ts=datetime.now(timezone.utc)
                    ))
                    db.session.commit()
                break
