from flask import Blueprint, render_template, request, redirect, url_for, abort, session
from .auth import login_required, admin_required
from app.models.sensor_reading import SensorReading
from app.extensions import db
from app.models.sensor import Sensor
from datetime import datetime, timedelta
import re

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

bp = Blueprint("sensor", __name__, template_folder="templates")

def make_temp_assessor(low_alert_max, green_max, yellow_max):
    return lambda v, _=None: (
        "red" if v < low_alert_max else
        "green" if v <= green_max else
        "yellow" if v <= yellow_max else "red"
    )

def make_range_assessor(green_max, yellow_max):
    return lambda v, _=None: (
        "green" if v < green_max else
        "yellow" if v < yellow_max else "red"
    )

def make_silo_assessor(low_alert_max, high_alert_min):
    return lambda v, _=None: (
        "red" if (v <= low_alert_max or v > high_alert_min) else "green"
    )

DEFAULTS_MAP = {
    "temperature": {
        "defaults": {"low_alert_max": 20, "green_max": 25, "yellow_max": 28},
        "assess":   make_temp_assessor(20, 25, 28),
    },
    "humidity": {
        "defaults": {"green_max": 15, "yellow_max": 20},
        "assess":   make_range_assessor(15, 20),
    },
    "silo": {
        "defaults": {"low_alert_max": 50, "high_alert_min": 400},
        "assess":   make_silo_assessor(50, 400),
    },
}

DEFAULT_SENSORS = [
    {**{
        "id": 1, "key": "temperature", "name": "Temperatura",
        "topic": "sensor", "icon": "bi-thermometer", "unit": "°C"
    }, **DEFAULTS_MAP["temperature"]},
    {**{
        "id": 2, "key": "humidity",    "name": "Umidade",
        "topic": "sensor", "icon": "bi-droplet-half", "unit": "%"
    }, **DEFAULTS_MAP["humidity"]},
    {**{
        "id": 3, "key": "silo",        "name": "Nível do Silo",
        "topic": "sensor", "icon": "bi-radar", "unit": ""
    }, **DEFAULTS_MAP["silo"]},
]

def ensure_default_sensors():
    created = False
    for d in DEFAULT_SENSORS:
        if not Sensor.query.filter_by(key=d["key"]).first():
            db.session.add(Sensor(
                key=d["key"], name=d["name"],
                topic="sensor", icon=d["icon"], unit=d["unit"]
            ))
            created = True
    if created:
        db.session.commit()

sensors: dict[str, dict] = {}

def initialize_sensors(app=None):
    sensors.clear()
    for d in DEFAULT_SENSORS:
        sensors[d["key"]] = {
            "id":        d["id"],
            "name":      d["name"],
            "topic":     "sensor",
            "icon":      d["icon"],
            "unit":      d["unit"],
            "defaults":  d["defaults"],
            "assess":    d["assess"],
            "value":     None,
            "color":     "secondary",
            "history":   [],
        }

try:
    initialize_sensors()
except RuntimeError:
    pass

@bp.route('/admin/sensors')
@login_required
@admin_required
def admin_list_sensors():
    return render_template('admin_sensors.html', sensors=sensors)

@bp.route('/admin/sensors/new')
@login_required
@admin_required
def admin_new_sensor():
    return render_template('admin_sensor_form.html', action='create')

@bp.route('/admin/sensors', methods=['POST'])
@login_required
@admin_required
def admin_create_sensor():
    topic = request.form['topic'].strip()
    key   = slugify(topic)

    if key in sensors:
        return render_template('admin_sensor_form.html', action='create',
                               error_msg='Já existe sensor com este tópico')

    new_sensor = Sensor(
        key=key, name=request.form['name'],
        topic=topic, icon=request.form['icon'],
        unit=request.form.get('unit', '')
    )
    db.session.add(new_sensor)
    db.session.commit()

    base = DEFAULTS_MAP.get(key, {"defaults": {}, "assess": lambda *_: "secondary"})
    sensors[key] = {
        "id": max(s["id"] for s in sensors.values()) + 1,
        "name": new_sensor.name,
        "topic": new_sensor.topic,
        "icon": new_sensor.icon,
        "unit": new_sensor.unit,
        "defaults": base["defaults"],
        "assess": base["assess"],
        "value": None,
        "color": "secondary",
        "history": [],
    }
    return redirect(url_for('sensor.sensor_detail', key=key))

@bp.route('/admin/sensors/<key>/edit')
@login_required
@admin_required
def admin_edit_sensor(key):
    if key not in sensors:
        abort(404)
    return render_template('admin_sensor_form.html',
                           action='edit', key=key, data=sensors[key])

@bp.route('/admin/sensors/<key>', methods=['POST'])
@login_required
@admin_required
def admin_update_sensor(key):
    if key not in sensors:
        abort(404)

    sensor = Sensor.query.filter_by(key=key).first_or_404()
    sensor.name  = request.form['name']
    sensor.topic = request.form['topic']
    sensor.icon  = request.form['icon']
    sensor.unit  = request.form.get('unit', '')
    db.session.commit()

    sensors[key].update({
        'name': sensor.name,
        'topic': sensor.topic,
        'icon': sensor.icon,
        'unit': sensor.unit,
    })
    return redirect(url_for('sensor.admin_list_sensors'))

@bp.route('/admin/sensors/<key>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_sensor(key):
    if key in ('temperature', 'humidity', 'silo'):
        abort(403)
    s = Sensor.query.filter_by(key=key).first()
    if s:
        db.session.delete(s)
        db.session.commit()
        sensors.pop(key, None)
    return redirect(url_for('sensor.admin_list_sensors'))

@bp.route('/sensor/<key>')
@login_required
def sensor_detail(key):
    if key not in sensors:
        abort(404)

    sensor_cfg = sensors[key]

    date_from = request.args.get('from')
    date_to   = request.args.get('to')
    query = SensorReading.query.filter_by(sensor_id=sensor_cfg['id'])

    if date_from:
        df = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(SensorReading.ts >= df)
    if date_to:
        dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(SensorReading.ts < dt)

    rows = query.order_by(SensorReading.ts.desc()).all()

    history = [{
        'ts': r.ts.strftime('%d/%m/%Y %H:%M:%S'),
        'value': r.value,
        'color': sensor_cfg['assess'](r.value, sensor_cfg['defaults'])
    } for r in rows]

    return render_template(
        'device_detail.html',
        device=sensor_cfg,
        dev_key=key,
        dev_type='sensor',
        history=history,
        is_admin=session.get('is_admin', False),
    )
