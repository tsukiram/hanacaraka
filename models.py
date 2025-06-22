# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from extensions import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image = db.Column(db.LargeBinary, nullable=True)  # BLOB untuk profile picture
    tests = db.relationship('TestResult', backref='user', lazy=True)
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True)

    def __init__(self, username, password_hash, profile_image=None):
        self.username = username
        self.password_hash = password_hash
        self.profile_image = profile_image

    def __repr__(self):
        return f'<User {self.username}>'

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)
    set_name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    messages = db.relationship('ChatMessage', backref='chat_session', lazy=True)

    def __repr__(self):
        return f'<ChatSession {self.title}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    input_raw = db.Column(db.Text)  # Input asli pengguna
    error_tags = db.Column(db.Text)  # Tag kesalahan
    correction_tags = db.Column(db.Text)  # Koreksi
    scores = db.Column(db.JSON)  # Skor struktur, diksi, konteks
    variants = db.Column(db.JSON)  # Varian kasual/formal
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.role}: {self.content[:50]}...>'