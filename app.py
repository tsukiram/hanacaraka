# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\app.py
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os
from extensions import db, csrf

# Initialize Flask app
app = Flask(__name__)
load_dotenv()

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "hanacaraka.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max upload size: 5MB for images/audio

# Ensure the instance and upload directories exist
instance_dir = os.path.join(basedir, 'instance')
upload_dir = os.path.join(basedir, 'static', 'uploads')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)

# Initialize extensions
db.init_app(app)
csrf.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Import models after db initialization
from models import User

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Import routes after app and db initialization
from routes.auth import auth
from routes.home import home
from routes.profile import profile
from routes.results import results
from routes.test_reading import test_reading
from routes.test_listening import test_listening
from routes.test_speaking import test_speaking
from routes.test_writing import test_writing
from routes.sinta import sinta
from routes.users import users

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(home)
app.register_blueprint(profile, url_prefix='/profile')
app.register_blueprint(results, url_prefix='/results')
app.register_blueprint(test_reading, url_prefix='/tests/reading')
app.register_blueprint(test_listening, url_prefix='/tests/listening')
app.register_blueprint(test_speaking, url_prefix='/tests/speaking')
app.register_blueprint(test_writing, url_prefix='/tests/writing')
app.register_blueprint(sinta, url_prefix='/sinta')
app.register_blueprint(users, url_prefix='/users')

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Disable caching for all responses
@app.after_request
def add_no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)