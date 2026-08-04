from flask import Flask, render_template, request, redirect, url_for, flash

from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint

from extensions import db

from models import User, Book, Message

from forms import ChatForm

chats_bp = Blueprint("chats", __name__)

'''
Book Details
↓
Borrow Book
↓
BorrowRequest created
↓
Automatic first message
↓
Chat page opens
↓
Owner and borrower discuss
↓
Owner approves/rejects from dashboard
'''
@chats_bp.route("/<username>/<int:book_id>")
@login_required
def chat(username, book_id):

    receiver = User.query.filter_by(username = username).first()

    if receiver is None:

        flash(
            "User not found,",
            "error"
        )
        return redirect(url_for("books.home"))

    form = ChatForm()

    book = db.session.get(Book, book_id)


    messages = Message.query.filter(
        Message.book_id == book.id
        ).filter(
        (
            (Message.sender_id == current_user.id)
            &
            (Message.receiver_id == receiver.id)
        )
            |
        (
            (Message.sender_id == receiver.id)
            &
            (Message.receiver_id == current_user.id)
        )
    ).order_by(Message.id).all()

    return render_template("chat/chat.html", form =form, messages=messages, receiver=receiver, book=book)

@chats_bp.route("/conversations")
@login_required
def conversations():

    messages = Message.query.filter(
        (Message.sender_id == current_user.id)
        |
        (Message.receiver_id == current_user.id)
    ).all()

    conversations = {}

    for msg in messages:

        if msg.sender_id == current_user.id:
            other_user = msg.receiver

        else:
            other_user = msg.sender

        key = (
            other_user.id,
            msg.book_id
        )

        conversations[key] = {
            "user": other_user,
            "book": msg.book
        }

    return render_template("chat/conversations.html", conversations=conversations.values())