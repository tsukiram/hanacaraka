from app import app
from extensions import db
from models import User, TestResult

with app.app_context():
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create new tables
    print("Database reinitialized successfully!")