from flask import Flask, render_template, request, redirect, url_for, flash

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from forms import RegistrationForm, LoginForm

from extensions import db

from flask import Blueprint

from models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        # filter_by takes keyword args
        existing_user = User.query.filter_by(username = form.username.data).first()

        if existing_user:
            flash(
                "Username already exists",
                "error"
            )

            return redirect(url_for("auth.register"))
        
        hashed_password = generate_password_hash(form.password.data)

        new_user = User(
            username = form.username.data,
            city = form.city.data, 
            password = hashed_password
            )
        
        db.session.add(new_user)
        db.session.commit()

        flash(
            "Account created successfully! Please login",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/registeruser.html", form=form)

@auth_bp.route("/login", methods = ["GET", "POST"])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username = form.username.data).first()

        if user is None:
            flash(
                "Username does not exist.",
                "error"
            )

        elif not check_password_hash(user.password, form.password.data):

            flash(
                "Incorrect password.",
                "error"
            )

        else:

            login_user(user)

            flash(
                f"Welcome back, {user.username}!",
                "success"
            )
            return redirect(url_for("books.home"))
        
    return render_template("auth/login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Logged out successfully",
        "success"
    )

    return redirect(url_for("auth.login"))
