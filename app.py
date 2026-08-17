from flask import Flask, render_template

from flask_login import current_user

from config import Config

from extensions import (
    db,
    login_manager,
    socketio,
    mail
)

from forms import *

from models import *

from flask_migrate import Migrate


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

login_manager.login_view = "auth.login" 
'''if user is not logged in while accessing @login_required routes, it redirects to "login" page'''

mail.init_app(app)


from routes.books import books_bp
from routes.auth import auth_bp
from routes.users import users_bp
from routes.dashboard import dashboard_bp
from routes.chat import chats_bp
from payments import payments_bp

import socket_events

app.register_blueprint(books_bp)

app.register_blueprint(auth_bp, url_prefix = "/auth")

app.register_blueprint(users_bp, url_prefix = "/user")

app.register_blueprint(dashboard_bp, url_prefix = "/dashboard")

app.register_blueprint(chats_bp, url_prefix = "/chat")

app.register_blueprint(payments_bp)


ERROR_PAGES = {
    403: ("lock", "This shelf is reserved", "That page belongs to someone else, so it's behind the librarian's desk. If you think you should have access, try signing in with the right account."),
    404: ("book-x", "This page wandered off the shelf", "We looked in every aisle but couldn't find what you were after. The book or reader may have been removed, or the link might be mistyped."),
    500: ("droplet", "We spilled some ink", "Something went wrong on our side. Nothing you did, and your books are safe. Please try again in a moment."),
}


def _error_page(error):

    code = getattr(error, "code", 500)

    if code not in ERROR_PAGES:
        code = 500

    if code == 500:
        db.session.rollback()

    glyph, heading, message = ERROR_PAGES[code]

    return render_template(
        "errors/error.html", code=code, glyph=glyph, heading=heading, message=message
    ), code


for _code in ERROR_PAGES:
    app.register_error_handler(_code, _error_page)


@app.context_processor
def inject_notif_count():

    if current_user.is_authenticated:

        unread_count = Notification.query.filter_by(user_id = current_user.id, read = False).count()

    else:

        unread_count = 0

    return dict(unread_count = unread_count)


@app.context_processor
def inject_asset_version():
    """Version stamp for the stylesheet so browsers re-fetch it whenever the file changes."""
    import os
    try:
        version = int(os.path.getmtime(os.path.join(app.static_folder, "css", "style.css")))
    except OSError:
        version = 0
    return dict(asset_version=version)


@app.context_processor
def inject_genres():
    from models import Genre
    return dict(genres=Genre.query.order_by(Genre.name).all())




if __name__=="__main__":
    socketio.run(app, debug=True, host="0.0.0.0", allow_unsafe_werkzeug=True)