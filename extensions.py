from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO


db = SQLAlchemy()

# LOGIN USER CONFIG
login_manager = LoginManager() 
'''gives these features: 
current_user
@login_required
login_user()
logout_user()'''

socketio = SocketIO()