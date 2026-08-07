from flask import render_template, flash, redirect, url_for

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

from models import BorrowRequestStatus, User, Notification, Message, BorrowRequest

from forms import EditProfileForm, ChangePasswordForm

from werkzeug.utils import secure_filename

import os

import uuid

from PIL import Image

users_bp = Blueprint("users", __name__)

@users_bp.route("/<username>")
@login_required
def profile(username):

    user = User.query.filter_by(username = username).first()

    return render_template("user/profile.html", user=user)

@users_bp.route("/notifications")
@login_required
def notifications():

    notifications = Notification.query.filter_by(user_id = current_user.id).order_by(Notification.timestamp.desc()).all()

    for notification in notifications:
        notification.read = True

    db.session.commit()

    return render_template("user/notifications.html", notifications=notifications)

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

        db.session.commit()

        flash(
            "Profile updated!",
            "success"
        )

        return redirect(url_for("users.profile", username=current_user.username))

    return render_template("user/edit_profile.html", form = form)
    
@users_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():

    user = User.query.get(current_user.id)
    
    logout_user()

    db.session.delete(user)
    

    messages_sent = Message.query.filter_by(sender_id = current_user.id).all()

    for msg in messages_sent:
        msg.sender_id = None

    messages_received = Message.query.filter_by(receiver_id = current_user.id).all()

    for msg in messages_received:
        msg.receiver_id = None

    db.session.commit()

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
        
        current_user.password = generate_password_hash(form.new_password.data)

        db.session.commit()

        flash(
            "Password changes successfully!",
            "success"
        )

        return redirect(url_for("users.profile", username=current_user.username))
    
    return render_template("user/change_password.html", form=form)

@users_bp.route("/my-borrow-requests")
@login_required
def my_borrow_requests():

    requests = BorrowRequest.query.filter_by(borrower_id=current_user.id).order_by(BorrowRequest.created_at.desc()).all()

    return render_template("user/my_borrow_requests.html", requests=requests, BorrowRequestStatus=BorrowRequestStatus)

    
    






