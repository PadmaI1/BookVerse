from flask import Flask

from flask_login import current_user

from config import Config

from extensions import (
    db,
    login_manager,
    socketio
)

from forms import *

from models import *

from flask_migrate import Migrate

import socket_events

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

migrate = Migrate(app, db)

socketio.init_app(app)

login_manager.init_app(app) 
''' Connects Flask-Login to YOUR Flask app
Now Flask-Login can:

✔ read requests
✔ access sessions
✔ create current_user
✔ intercept routes
✔ manage login state

for THIS specific app. '''

login_manager.login_view = "login" 
'''if user is not logged in while accessing @login_required routes, it redirects to "login" page'''


from routes.books import books_bp
from routes.auth import auth_bp
from routes.users import users_bp
from routes.dashboard import dashboard_bp
from routes.chat import chats_bp

app.register_blueprint(books_bp)

app.register_blueprint(auth_bp, url_prefix = "/auth")

app.register_blueprint(users_bp, url_prefix = "/user")

app.register_blueprint(dashboard_bp, url_prefix = "/dashboard")

app.register_blueprint(chats_bp, url_prefix = "/chat")


@app.context_processor
def inject_notif_count():

    if current_user.is_authenticated:

        unread_count = Notification.query.filter_by(user_id = current_user.id, read = False).count()

    else:

        unread_count = 0

    return dict(unread_count = unread_count)




if __name__=="__main__":
    socketio.run(app, debug=True)