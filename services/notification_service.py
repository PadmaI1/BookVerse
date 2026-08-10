from models import Notification

from extensions import db

def create_notification(user_id, message, link=""):
    notification = Notification(
        user_id=user_id,
        notif=message,
        link=link or ""
    )

    db.session.add(notification)
    db.session.commit()
