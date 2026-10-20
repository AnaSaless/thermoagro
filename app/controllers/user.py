from flask import Blueprint, request, redirect, url_for, render_template, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from app.controllers.auth import login_required, admin_required
from app.models.user import User, Role
from app.extensions import db

user = Blueprint("user", __name__, template_folder="templates")

def get_user_by_username_or_email(ident):
    return User.query.filter(
        (User.username == ident) | (User.email == ident)
    ).first()

def is_email_taken(email, exclude_username=None):
    q = User.query.filter_by(email=email)
    if exclude_username:
        q = q.filter(User.username != exclude_username)
    return q.first() is not None

def is_username_taken(username):
    return User.query.filter_by(username=username).first() is not None

@user.route('/validated_user', methods=['POST'])
def validated_user():
    ident = request.form['user']
    pwd   = request.form['password']

    user_obj = get_user_by_username_or_email(ident)
    if user_obj and check_password_hash(user_obj.password, pwd):
        session['user']      = user_obj.username
        session['email']     = user_obj.email
        session['is_admin']  = user_obj.is_admin
        session['function']  = user_obj.function
        session['user_id']   = user_obj.id
        return redirect(url_for('main.home'))  # Correção da rota

    return render_template('login.html',
                           error_msg='Usuário/e-mail ou senha incorretos')

@user.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))  # Correção da rota

@user.route('/admin/users')
@login_required
@admin_required
def admin_list_users():
    users_db = User.query.all()
    users = {
        u.username: {
            'email': u.email,
            'is_admin': u.is_admin
        }
        for u in users_db
    }
    return render_template('admin_users.html', users=users)

@user.route('/admin/users/new')
@login_required
@admin_required
def admin_new_user():
    return render_template('admin_user_form.html', action='create')

@user.route('/admin/users', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    username = request.form['user']
    email    = request.form['email']
    pwd      = request.form['password']
    is_admin = request.form.get('is_admin') == 'on'

    if is_username_taken(username) or is_email_taken(email):
        return render_template('admin_user_form.html', action='create',
                               error_msg='Username ou e-mail já existe')

    role = Role.query.filter_by(name='Admin' if is_admin else 'User').first()
    if not role:
        role = Role(name='Admin' if is_admin else 'User')
        db.session.add(role)
        db.session.commit()

    db.session.add(User(username=username,
                        email=email,
                        password=generate_password_hash(pwd),
                        role=role,
                        function='admin' if is_admin else 'user'))
    db.session.commit()
    return redirect(url_for('user.admin_list_users'))

@user.route('/admin/users/<username>/edit')
@login_required
@admin_required
def admin_edit_user(username):
    u = User.query.filter_by(username=username).first_or_404()
    return render_template('admin_user_form.html',
                           action='edit', username=username, data=u)

@user.route('/admin/users/<username>', methods=['POST'])
@login_required
@admin_required
def admin_update_user(username):
    u = User.query.filter_by(username=username).first_or_404()
    email    = request.form['email']
    pwd      = request.form['password']
    is_admin = request.form.get('is_admin') == 'on'

    if is_email_taken(email, exclude_username=username):
        return render_template('admin_user_form.html',
                               action='edit', username=username, data=u,
                               error_msg='E-mail já cadastrado em outro usuário')

    u.email = email
    u.role  = Role.query.filter_by(name='Admin' if is_admin else 'User').first()
    if pwd:
        u.password = generate_password_hash(pwd)
    db.session.commit()
    return redirect(url_for('user.admin_list_users'))

@user.route('/admin/users/<username>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(username):
    if username == 'admin':
        abort(403)
    u = User.query.filter_by(username=username).first_or_404()
    db.session.delete(u)
    db.session.commit()
    return redirect(url_for('user.admin_list_users'))

# Alias opcional para compatibilidade com app.register_blueprint(user.bp)
bp = user
