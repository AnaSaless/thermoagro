from flask import Blueprint, session, redirect, url_for, abort
from functools import wraps

bp = Blueprint('auth', __name__)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('main.index'))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            abort(403)
        return fn(*args, **kwargs)
    return wrapper




