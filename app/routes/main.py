from flask import Blueprint, render_template, current_app
from flask_login import current_user
from app.controllers.auth import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template("login.html")

@main_bp.route("/home")
@login_required
def home():
    return render_template("home.html", wokwi_url=current_app.config.get("WOKWI_URL", ""))

@main_bp.app_errorhandler(403)
def _403(error):
    return render_template("errors/403.html"), 403

@main_bp.app_errorhandler(404)
def _404(error):
    return render_template("errors/404.html"), 404

@main_bp.app_errorhandler(500)
def _500(error):
    return render_template("errors/500.html"), 500
