import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user  # Added current_user
from models import User
from extensions import db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not all([username, password]):
            flash('Missing username or password')
            logger.error('Login attempt with missing username or password')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.debug(f"User {username} logged in successfully")
            next_page = request.args.get('next', url_for('tests.home'))
            return redirect(next_page)
        flash('Invalid username or password')
        logger.error(f"Failed login attempt for username: {username}")
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not all([username, password]):
            flash('Missing username or password')
            logger.error('Registration attempt with missing username or password')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            logger.error(f"Registration failed: Username {username} already exists")
            return render_template('register.html')
        
        try:
            new_user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            logger.debug(f"User {username} registered successfully")
            return redirect(url_for('auth.login'))
        except Exception as db_error:
            db.session.rollback()
            flash('Error during registration. Please try again.')
            logger.error(f"Database error during registration: {str(db_error)}")
            return render_template('register.html')
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logger.debug(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for('auth.login'))