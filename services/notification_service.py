from models import Notification

from extensions import db

def create_notification(user_id, message, link):
    notification = Notification(
        user_id=user_id,
        message=message,
        link=link
    )

    db.session.add(notification)
