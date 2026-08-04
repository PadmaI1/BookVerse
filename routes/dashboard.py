from flask import Flask, render_template, request, redirect, url_for, flash

from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint

from models import BorrowRequest, Book, Notification

from extensions import db


dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def dashboard():

    requests = BorrowRequest.query.join(Book).filter(Book.user_id == current_user.id).all()

    return render_template("dashboard/dashboard.html", requests=requests)

@dashboard_bp.route("/request/approve/<int:request_id>", methods = ["POST"])
@login_required
def approve_request(request_id):

    request_obj = db.session.get(BorrowRequest, request_id)

    if request_obj is None:

        flash(
            "No such request exists!",
            "error"
        )
        return redirect(url_for("dashboard.dashboard"))

    if request_obj.book.user_id != current_user.id:

        flash(
            f"You can't approve this request as you are no the owner of '{request_obj.book.title}'",
            "error"
        )
        return redirect(url_for("books.home"))
    
    request_obj.status = "approved"

    flash(
        "Borrow request approved!",
        "success"
    )

    request_obj.book.availability = False

    notif = Notification(
        user_id = request_obj.borrower_id,
        notif = f"{request_obj.book.user.username} approved your request for book: {request_obj.book.title}",
        link = url_for("chats.chat", username=request_obj.book.user.username, id=request_obj.book.id)
    )

    db.session.add(notif)

    db.session.commit()

    return redirect(url_for("dashboard.dashboard"))

@dashboard_bp.route("/request/reject/<int:request_id>", methods = ["POST"])
@login_required
def reject_request(request_id):

    request_obj = db.session.get(BorrowRequest, request_id)

    if request_obj is None:

        flash(
            "No suck request exists!",
            "error"
        )
        return redirect(url_for("dashboard.dashboard"))

    if request_obj.book.user_id != current_user.id:

        flash(
            f"You can't reject this request as you are no the owner of '{request_obj.book.title}'",
            "error"
        )
        return redirect(url_for("books.home"))
    
    request_obj.status = "rejected"

    flash(
        "Borrow request rejected",
        "success"
    )

    notif = Notification(
        user_id = request_obj.borrower_id,
        notif = f"{request_obj.book.user.username} rejected your request for book: {request_obj.book.title}"
    )

    db.session.add(notif)

    db.session.commit()

    return redirect(url_for("dashboard.dashboard"))
