from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, abort

from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint

from extensions import db

from models import User, Book, Message, BorrowRequest

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
def _conversation_list():
    """One entry per (other user, book), newest conversation first."""
    messages = Message.query.filter(
        (Message.sender_id == current_user.id)
        |
        (Message.receiver_id == current_user.id)
    ).order_by(Message.id).all()

    conversations = {}

    for msg in messages:
        other_user = msg.receiver if msg.sender_id == current_user.id else msg.sender

        conversations[(other_user.id if other_user else None, msg.book_id)] = {
            "user": other_user,
            "book": msg.book,
            "last": msg,
            "mine": msg.sender_id == current_user.id,
            "lending": msg.book.owner_id == current_user.id,
        }

    return sorted(conversations.values(), key=lambda c: c["last"].id, reverse=True)


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

    if book is None:
        abort(404)

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

    is_owner = book.owner_id == current_user.id
    borrower_id = receiver.id if is_owner else current_user.id
    borrow_request = BorrowRequest.query.filter_by(book_id=book.id, borrower_id=borrower_id).order_by(BorrowRequest.id.desc()).first()

    return render_template(
        "chat/chat.html",
        form=form,
        messages=messages,
        receiver=receiver,
        book=book,
        is_owner=is_owner,
        borrow_request=borrow_request,
        conversations=_conversation_list(),
        today=datetime.utcnow().date(),
    )

@chats_bp.route("/conversations")
@login_required
def conversations():

    return render_template("chat/conversations.html", conversations=_conversation_list(), today=datetime.utcnow().date())
