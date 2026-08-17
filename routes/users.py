from collections import Counter
from datetime import datetime

from flask import render_template, flash, redirect, url_for, abort

from flask_login import (
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask import Blueprint, current_app

from extensions import db

from sqlalchemy import func

from models import BorrowRequestStatus, User, Notification, Message, BorrowRequest, Book, Payment

from forms import EditProfileForm, ChangePasswordForm, DeleteAccountForm

from werkzeug.utils import secure_filename

import os

import uuid

from PIL import Image

users_bp = Blueprint("users", __name__)

LEVELS = [
    (0, "New reader", "📖"),
    (4, "Bookmarker", "🔖"),
    (10, "Bookworm", "📚"),
    (20, "Shelf keeper", "🏛️"),
    (35, "Head librarian", "👑"),
]


@users_bp.route("/<username>")
@login_required
def profile(username):

    user = User.query.filter_by(username = username).first()

    if user is None:
        abort(404)

    is_self = current_user.id == user.id
    books = sorted(user.books, key=lambda b: b.id, reverse=True)
    book_ids = [b.id for b in books]

    # loans per book, completed lends, and (for the owner only) who currently has each book
    loans = {}
    returned_lends = 0
    holders = {}
    if book_ids:
        rows = db.session.query(BorrowRequest.book_id, BorrowRequest.status, func.count()).filter(
            BorrowRequest.book_id.in_(book_ids)
        ).group_by(BorrowRequest.book_id, BorrowRequest.status).all()
        for book_id, status, n in rows:
            if status in (BorrowRequestStatus.ACTIVE, BorrowRequestStatus.RETURNED):
                loans[book_id] = loans.get(book_id, 0) + n
            if status == BorrowRequestStatus.RETURNED:
                returned_lends += n
        if is_self:
            for req in BorrowRequest.query.filter(
                BorrowRequest.book_id.in_(book_ids), BorrowRequest.status == BorrowRequestStatus.ACTIVE
            ).all():
                holders[req.book_id] = req.borrower.username

    borrowed_returned = BorrowRequest.query.filter_by(borrower_id=user.id, status=BorrowRequestStatus.RETURNED).count()
    borrowing_now = []
    if is_self:
        borrowing_now = BorrowRequest.query.filter_by(borrower_id=user.id, status=BorrowRequestStatus.ACTIVE).all()

    available = sum(1 for b in books if b.availability)

    # a playful reader level based on real activity
    score = len(books) * 2 + returned_lends * 3 + borrowed_returned * 2
    level_idx = max(i for i, (need, _, _) in enumerate(LEVELS) if score >= need)
    level = {"name": LEVELS[level_idx][1], "emoji": LEVELS[level_idx][2], "number": level_idx + 1}
    if level_idx + 1 < len(LEVELS):
        need_next = LEVELS[level_idx + 1][0]
        base = LEVELS[level_idx][0]
        level["next"] = LEVELS[level_idx + 1][1]
        level["to_go"] = need_next - score
        level["pct"] = int(100 * (score - base) / (need_next - base))
    else:
        level["next"] = None
        level["to_go"] = 0
        level["pct"] = 100

    genre_counts = Counter(b.genre for b in books)
    fav_genres = genre_counts.most_common(4)

    badges = [
        {"name": "First book shared", "emoji": "📘", "desc": "Put a book on the shelf.", "earned": len(books) >= 1},
        {"name": "Generous lender", "emoji": "🤝", "desc": "Share 5 or more books.", "earned": len(books) >= 5},
        {"name": "Safe returns", "emoji": "🛡️", "desc": "Complete a loan with a refunded deposit.", "earned": (returned_lends + borrowed_returned) >= 1},
        {"name": "Genre explorer", "emoji": "🧭", "desc": "Share books in 3 different genres.", "earned": len(genre_counts) >= 3},
        {"name": "Verified reader", "emoji": "✅", "desc": "Confirmed their email address.", "earned": bool(user.email_verified)},
    ]

    return render_template(
        "user/profile.html",
        user=user,
        is_self=is_self,
        books=books,
        loans=loans,
        holders=holders,
        stats={
            "books": len(books),
            "available": available,
            "on_loan": len(books) - available,
            "completed": returned_lends + borrowed_returned,
        },
        level=level,
        score=score,
        fav_genres=fav_genres,
        badges=badges,
        borrowing_now=borrowing_now,
    )

# (label, icon, colour group) for each kind of notification, worked out from its text
NOTIFICATION_KINDS = {
    "request": ("Borrow request", "bookmark-plus", "brass"),
    "approved": ("Request approved", "check-circle", "primary"),
    "declined": ("Request declined", "x-circle", "leather"),
    "message": ("New message", "message-circle", "ink"),
    "deposit": ("Deposit", "shield-check", "primary"),
    "refund": ("Deposit refund", "badge-check", "primary"),
    "general": ("Update", "bell", "ink"),
}
NOTIFICATION_GROUPS = {
    "requests": ("request", "approved", "declined"),
    "messages": ("message",),
    "deposits": ("deposit", "refund"),
}


def _notification_kind(text):
    t = text.lower()
    if "refund" in t:
        return "refund"
    if "message from" in t:
        return "message"
    if "approved" in t:
        return "approved"
    if "rejected" in t or "declined" in t:
        return "declined"
    if "requested" in t:
        return "request"
    if "deposit" in t or "paid" in t or "payment" in t:
        return "deposit"
    return "general"


def _time_ago(moment):
    seconds = (datetime.utcnow() - moment).total_seconds()
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    if seconds < 172800:
        return "Yesterday"
    return moment.strftime("%d %b")


@users_bp.route("/notifications")
@login_required
def notifications():

    rows = Notification.query.filter_by(user_id = current_user.id).order_by(Notification.timestamp.desc()).all()

    items = []
    for n in rows:
        kind = _notification_kind(n.notif)
        label, icon_name, tone = NOTIFICATION_KINDS[kind]
        group = next((g for g, kinds in NOTIFICATION_GROUPS.items() if kind in kinds), "other")
        items.append({"n": n, "kind": kind, "label": label, "icon": icon_name, "tone": tone, "group": group, "ago": _time_ago(n.timestamp)})

    counts = {
        "all": len(items),
        "unread": sum(1 for i in items if not i["n"].read),
        "requests": sum(1 for i in items if i["group"] == "requests"),
        "messages": sum(1 for i in items if i["group"] == "messages"),
        "deposits": sum(1 for i in items if i["group"] == "deposits"),
    }

    return render_template("user/notifications.html", items=items, counts=counts)


@users_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def notifications_read_all():

    Notification.query.filter_by(user_id = current_user.id, read = False).update({"read": True})
    db.session.commit()

    return redirect(url_for("users.notifications"))


@users_bp.route("/notifications/<int:notification_id>/open")
@login_required
def notification_open(notification_id):
    """Mark one notification as read, then go to the page it points at."""

    n = db.session.get(Notification, notification_id)

    if n is None or n.user_id != current_user.id:
        abort(404)

    n.read = True
    db.session.commit()

    target = n.link or ""
    if target.startswith("/") and not target.startswith("//"):
        return redirect(target)

    return redirect(url_for("users.notifications"))

@users_bp.route("/profile/edit", methods = ["GET", "POST"])
@login_required
def edit_profile():

    form = EditProfileForm(obj = current_user)

    if form.validate_on_submit():

        existing_user = User.query.filter_by(username = form.username.data).first()

        if existing_user and existing_user.id != current_user.id:
            flash(
                "Username already exists",
                "error"
            )

            return redirect(url_for("users.edit_profile"))
        
        picture = form.profile_pic.data

        if picture:

            filename = secure_filename(picture.filename)
            
            unique_filename = str(uuid.uuid4()) + "_" + filename

            old_pic = current_user.profile_pic

            if old_pic != "default.jpg":

                old_path = os.path.join(current_app.root_path, "static", "profile_pics", old_pic)

                if os.path.exists(old_path):
                    os.remove(old_path)

            path = os.path.join(current_app.root_path, "static", "profile_pics", unique_filename)

            img = Image.open(picture)
            img.thumbnail((300, 300))
            img.save(path)

            current_user.profile_pic = unique_filename

        
        current_user.username = form.username.data
        current_user.city = form.city.data
        current_user.about = (form.about.data or "").strip()

        db.session.commit()

        flash(
            "Profile updated!",
            "success"
        )

        return redirect(url_for("users.profile", username=current_user.username))

    return render_template(
        "user/edit_profile.html",
        form = form,
        delete_form = DeleteAccountForm(),
        open_loans = _open_loans(current_user.id)
    )
    
def _open_loans(user_id):
    """Loans still in flight (approved or active) where the user is borrower or owner."""

    live = (BorrowRequestStatus.APPROVED, BorrowRequestStatus.ACTIVE)

    as_borrower = BorrowRequest.query.filter(
        BorrowRequest.borrower_id == user_id, BorrowRequest.status.in_(live)
    ).count()

    as_owner = BorrowRequest.query.join(Book, BorrowRequest.book_id == Book.id).filter(
        Book.owner_id == user_id, BorrowRequest.status.in_(live)
    ).count()

    return as_borrower + as_owner


@users_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():

    form = DeleteAccountForm()
    user = db.session.get(User, current_user.id)

    if not form.validate_on_submit() or form.confirm.data.strip() != user.username:
        flash("Type your username exactly to confirm deleting your account", "error")
        return redirect(url_for("users.edit_profile"))

    # a deposit may be held against an unfinished loan, so those have to be settled first
    if _open_loans(user.id):
        flash("Finish or return your open loans before deleting your account", "error")
        return redirect(url_for("users.edit_profile"))

    user_id = user.id
    pic = user.profile_pic

    # chat history stays for the other person, anonymised
    Message.query.filter_by(sender_id = user_id).update({"sender_id": None})
    Message.query.filter_by(receiver_id = user_id).update({"receiver_id": None})

    # everything hanging off the user's own books goes with them
    book_ids = [b.id for b in user.books]

    if book_ids:
        Message.query.filter(Message.book_id.in_(book_ids)).delete(synchronize_session=False)
        Payment.query.filter(Payment.book_id.in_(book_ids)).delete(synchronize_session=False)
        BorrowRequest.query.filter(BorrowRequest.book_id.in_(book_ids)).delete(synchronize_session=False)

    logout_user()

    db.session.delete(user)
    db.session.commit()

    if pic and pic != "default.jpg":
        pic_path = os.path.join(current_app.root_path, "static", "profile_pics", pic)

        if os.path.exists(pic_path):
            os.remove(pic_path)

    flash("Your account has been deleted. We're sorry to see you go.", "success")

    return redirect(url_for("auth.register"))

@users_bp.route("/profile/change-password", methods=['GET', 'POST'])
@login_required
def change_password():

    form = ChangePasswordForm()

    if form.validate_on_submit():

        if not check_password_hash(current_user.password, form.current_password.data):

            flash(
                "Current password is incorrect",
                "error"
            )

            return redirect(url_for("users.change_password"))
        
        if check_password_hash(current_user.password, form.new_password.data):

            flash(
                "Your new password must be different from the current one",
                "error"
            )

            return redirect(url_for("users.change_password"))

        current_user.password = generate_password_hash(form.new_password.data)

        db.session.commit()

        flash(
            "Password changed successfully!",
            "success"
        )

        return redirect(url_for("users.profile", username=current_user.username))
    
    return render_template("user/change_password.html", form=form)

@users_bp.route("/my-borrow-requests")
@login_required
def my_borrow_requests():

    requests = BorrowRequest.query.filter_by(borrower_id=current_user.id).order_by(BorrowRequest.created_at.desc()).all()

    group_of = {
        BorrowRequestStatus.PENDING: "pending",
        BorrowRequestStatus.APPROVED: "active",
        BorrowRequestStatus.ACTIVE: "active",
        BorrowRequestStatus.RETURNED: "done",
        BorrowRequestStatus.REJECTED: "done",
    }

    holding = [r for r in requests if r.status == BorrowRequestStatus.ACTIVE]

    stats = {
        "total": len(requests),
        "pending": sum(1 for r in requests if group_of[r.status] == "pending"),
        "active": sum(1 for r in requests if group_of[r.status] == "active"),
        "done": sum(1 for r in requests if group_of[r.status] == "done"),
        "with_you": len(holding),
        "held": sum(r.book.security_deposit for r in holding),
        "to_pay": sum(1 for r in requests if r.status == BorrowRequestStatus.APPROVED),
    }

    return render_template("user/my_borrow_requests.html", requests=requests, group_of=group_of, stats=stats, BorrowRequestStatus=BorrowRequestStatus)

    
    






