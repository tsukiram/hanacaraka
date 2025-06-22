# routes/home.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

home = Blueprint('home', __name__)

@home.route('/')
@login_required
def home_page():
    logger.debug(f"User {current_user.id} accessed home route")
    return render_template('home.html')