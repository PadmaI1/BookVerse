from flask import url_for
from flask_socketio import emit, join_room

from flask_login import (
    current_user
)

from models import Message, User, Book, Notification

from extensions import db

from extensions import socketio


@socketio.on("connect")
def handle_connect():
    print("A user connected!")

@socketio.on("join_room")
def handle_join_room(data):

    room = data["room"]

    join_room(room)

    print(f"User joined {room}")

@socketio.on("send_message")
def handle_send_message(data):

    receiver = db.session.get(User, data["receiver_id"])

    book = db.session.get(Book, data["book_id"])
    
    msg = Message(
    sender_id = current_user.id,
    receiver_id = data["receiver_id"],
    book_id = data["book_id"],
    content = data["content"]
    )

    db.session.add(msg)

    notification = Notification(
    user_id = receiver.id,
    notif = f"New message from {current_user.username} regarding {book.title}.",
    link = url_for("chats.chat", username=current_user.username, book_id=book.id)
    )

    db.session.add(notification)

    db.session.commit()

    smaller = min(current_user.id, data["receiver_id"])
    larger = max(current_user.id, data["receiver_id"])


    room = f"chat_{smaller}_{larger}_{data['book_id']}"
    print(room)

    emit(
        "new-message",
        {
            "content": msg.content,
            "sender_id": msg.sender_id,
            "timestamp": msg.timestamp.strftime("%d %b %Y %I:%M %p")
        },
        room=room
    )

