from flask_mail import Message
from extensions import mail

from flask import current_app, url_for

from itsdangerous import URLSafeTimedSerializer, SignatureExpired,BadSignature

def generate_verification_token(email):

    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(email)

def verify_token(token):

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    return serializer.loads(token, max_age=3600)

def send_verification_email(user):

    token = generate_verification_token(user.email)

    verification_url = current_app.config["BASE_URL"] +url_for("auth.verify_email", token=token)

    msg = Message(
        subject="Verify your BookVerse account",
        recipients=[user.email]
    )

    msg.body = f"""
    Hi {user.username},

    Welcome to BookVerse!

    Click the link below to verify your email.

    { verification_url }

    Thanks,
    BookVerse
    """

    mail.send(msg)