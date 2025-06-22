# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\routes\users.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Friendship
from extensions import db
import logging

logger = logging.getLogger(__name__)

users = Blueprint('users', __name__)

@users.route('/')
@login_required
def users_page():
    try:
        friends = Friendship.query.filter_by(user_id=current_user.id).all()
        return render_template('users.html', friends=friends)
    except Exception as e:
        logger.error(f"Error loading users page: {str(e)}", exc_info=True)
        return render_template('users.html', friends=[], error=str(e))