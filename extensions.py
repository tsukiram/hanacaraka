# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()