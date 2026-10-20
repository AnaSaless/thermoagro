from flask import Blueprint, render_template, request, redirect, url_for, abort, current_app, jsonify, session
from .auth import login_required, admin_required
from app.extensions import db
from app.models.actuator import Actuator
from app.models.actuator_history import ActuatorHistory
from app.models.user import User
import json
import importlib
import re
from datetime import datetime, timezone, timedelta

bp = Blueprint('actuator', __name__, template_folder='templates')

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def ensure_servo_actuator():
    if not Actuator.query.filter_by(key='servo').first():
        db.session.add(Actuator(
            key='servo', name='Porta do Silo', topic='servo',
            icon='bi-box-arrow-in-down-left',
            open_payload=json.dumps({'servo': 180}),
            close_payload=json.dumps({'servo': 90})
        ))
        db.session.commit()

@bp.route('/silo')
@login_required
def silo_page():
    servo = Actuator.query.filter_by(key='servo').first()
    silo  = current_app.config.get('sensors', {}).get(
            'silo', {'value': 0, 'color': 'gray'})
    return render_template(
        'silo.html',
        current_user=session['user'],
        silo=silo['value'],
        silo_color=silo['color'],
        is_open=current_app.config.get('SERVO_ANGLE', 90) == 180
    )

@bp.route('/admin/actuators')
@login_required
@admin_required
def admin_list_actuators():
    actuators = Actuator.query.all()
    data = {
        a.key: {
            'name': a.name,
            'topic': a.topic,
            'icon': a.icon,
            'open_payload': a.get_open_payload(),
            'close_payload': a.get_close_payload(),
        }
        for a in actuators
    }
    return render_template('admin_actuators.html', actuators=data)

@bp.route('/admin/actuators/new')
@login_required
@admin_required
def admin_new_actuator():
    return render_template('admin_actuator_form.html', action='create')

@bp.route('/admin/actuators', methods=['POST'])
@login_required
@admin_required
def admin_create_actuator():
    topic = request.form['topic'].strip()
    key = slugify(topic)

    if Actuator.query.filter_by(key=key).first():
        return render_template(
            'admin_actuator_form.html',
            action='create',
            error_msg='Já existe atuador com este tópico',
        )

    try:
        open_pl = json.loads(request.form['open_payload'])
        close_pl = json.loads(request.form['close_payload'])
    except json.JSONDecodeError:
        return render_template(
            'admin_actuator_form.html',
            action='create',
            error_msg='Payloads devem ser JSON válido',
        )

    new_actuator = Actuator(
        key=key,
        name=request.form['name'],
        topic=topic,
        icon=request.form['icon'],
        open_payload=json.dumps(open_pl),
        close_payload=json.dumps(close_pl),
    )
    db.session.add(new_actuator)
    db.session.commit()
    return redirect(url_for('actuator.actuator_detail', key=key))

@bp.route('/admin/actuators/<key>/edit')
@login_required
@admin_required
def admin_edit_actuator(key):
    actuator = Actuator.query.filter_by(key=key).first_or_404()
    data = {
        'name': actuator.name,
        'topic': actuator.topic,
        'icon': actuator.icon,
        'open_payload': actuator.get_open_payload(),
        'close_payload': actuator.get_close_payload(),
    }
    return render_template(
        'admin_actuator_form.html', action='edit', key=key, data=data
    )

@bp.route('/admin/actuators/<key>', methods=['POST'])
@login_required
@admin_required
def admin_update_actuator(key):
    actuator = Actuator.query.filter_by(key=key).first_or_404()
    actuator.name = request.form['name']
    actuator.topic = request.form['topic']
    actuator.icon = request.form['icon']

    try:
        open_pl = json.loads(request.form['open_payload'])
        close_pl = json.loads(request.form['close_payload'])
    except json.JSONDecodeError:
        data = {
            'name': actuator.name,
            'topic': actuator.topic,
            'icon': actuator.icon,
            'open_payload': actuator.get_open_payload(),
            'close_payload': actuator.get_close_payload(),
        }
        return render_template(
            'admin_actuator_form.html',
            action='edit',
            key=key,
            data=data,
            error_msg='Payloads devem ser JSON válido',
        )

    actuator.open_payload = json.dumps(open_pl)
    actuator.close_payload = json.dumps(close_pl)
    db.session.commit()
    return redirect(url_for('actuator.admin_list_actuators'))

@bp.route('/admin/actuators/<key>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_actuator(key):
    if key == 'servo':
        abort(403)
    actuator = Actuator.query.filter_by(key=key).first_or_404()
    db.session.delete(actuator)
    db.session.commit()
    return redirect(url_for('actuator.admin_list_actuators'))

@bp.route('/actuator/<key>/<action>', methods=['POST'])
@login_required
def trigger_actuator(key, action):
    actuator = Actuator.query.filter_by(key=key).first_or_404()
    if action not in ('open', 'close'):
        abort(400)

    payload = actuator.get_open_payload() if action == 'open' else actuator.get_close_payload()
    mqtt = current_app.config.get('MQTT_CLIENT') or importlib.import_module('app').mqtt
    mqtt.publish(actuator.topic, json.dumps(payload))

    if session.get('function') == 'operator':
        uid = session.get('user_id') or User.query.filter_by(username=session.get('user')).first().id
        db.session.add(ActuatorHistory(
            actuator_key=key,
            user_id=uid,
            action=action,
            ts=datetime.now(timezone.utc)
        ))
        db.session.commit()

    if key == 'servo':
        current_app.config['SERVO_ANGLE'] = 180 if action == 'open' else 90

    return jsonify({'status': 'ok'})

@bp.route('/actuator/<key>')
@login_required
def actuator_detail(key):
    actuator = Actuator.query.filter_by(key=key).first_or_404()
    device = {
        'name': actuator.name,
        'topic': actuator.topic,
        'icon': actuator.icon,
        'open_payload': actuator.get_open_payload(),
        'close_payload': actuator.get_close_payload(),
    }

    history = []
    if session.get('function') == 'operator' or session.get('is_admin'):
        q = ActuatorHistory.query.filter_by(actuator_key=key)

        # intervalo de datas
        date_from = request.args.get('from')
        date_to   = request.args.get('to')
        if date_from:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            q = q.filter(ActuatorHistory.ts >= df)
        if date_to:
            dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            q = q.filter(ActuatorHistory.ts < dt)

        rows = q.order_by(ActuatorHistory.ts.desc()).all()
        for r in rows:
            history.append({
                'ts': r.ts.strftime('%d/%m/%Y %H:%M:%S'),
                'value': 'ABRIR' if r.action == 'open' else 'FECHAR',
                'color': 'green' if r.action == 'open' else 'yellow'
            })

    return render_template(
        'device_detail.html',
        device=device, dev_key=key, dev_type='actuator',
        history=history,
        is_admin=session.get('is_admin', False)
    )

def get_actuators_dict():
    return {
        a.key: {
            'name': a.name,
            'topic': a.topic,
            'icon': a.icon,
            'open_payload': a.get_open_payload(),
            'close_payload': a.get_close_payload(),
        } for a in Actuator.query.all()
    }
