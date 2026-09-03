from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app

from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint

from forms import BookForm

from models import Book, Genre, BorrowRequest, BorrowRequestStatus, Message, Notification

from extensions import db

from services.notification_service import create_notification

import requests


books_bp = Blueprint("books", __name__)


def _genre_choices():
    return [(g.id, g.name) for g in Genre.query.order_by(Genre.name).all()]


@books_bp.route("/")
def home():
    books = Book.query.all()
    return render_template("book/home.html", books=books)


@books_bp.route("/book/add", methods=["GET", "POST"])
@login_required
def add_book():
    form = BookForm()
    form.genre.choices = _genre_choices()

    if form.validate_on_submit():
        new_book = Book(
            title=form.title.data,
            author=form.author.data,
            genre_id=form.genre.data,
            description=form.description.data,
            image=form.image.data,
            rating=form.rating.data,
            security_deposit=form.security_deposit.data,
            owner_id=current_user.id
        )

        db.session.add(new_book)
        db.session.commit()

        flash("Book added successfully!", "success")

        return redirect(url_for("books.home"))

    return render_template("book/addbook.html", form=form)


@books_bp.route("/book/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book.owner_id != current_user.id:
        flash("Can't delete book that doesn't belong to you", "error")
        return redirect(url_for("books.home"))

    if book:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted.", "success")

    return redirect(url_for("books.home"))


@books_bp.route("/book/edit/<int:book_id>", methods=["GET", "POST"])
@login_required
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    if book.owner_id != current_user.id:
        return redirect(url_for("books.home"))

    form = BookForm()
    form.genre.choices = _genre_choices()

    if request.method == "GET":
        form.title.data = book.title
        form.author.data = book.author
        form.genre.data = book.genre_id
        form.description.data = book.description
        form.image.data = book.image
        form.rating.data = book.rating
        form.security_deposit.data = book.security_deposit

    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.genre_id = form.genre.data
        book.description = form.description.data
        book.image = form.image.data
        book.rating = form.rating.data

        db.session.commit()

        flash("Book updated successfully!", "success")

        return redirect(url_for("books.home"))

    return render_template("book/editbook.html", form=form)


@books_bp.route("/book/genre/<int:genre_id>")
def books_genre(genre_id):
    genre = db.session.get(Genre, genre_id)

    if genre is None:
        flash("Genre not found.", "error")
        return redirect(url_for("books.home"))

    return render_template("book/genre.html", books=genre.books, genre=genre)


@books_bp.route("/book/<int:book_id>")
def book_details(book_id):
    book = db.session.get(Book, book_id)
    return render_template("book/book.html", book=book)


@books_bp.route("/book/request/<int:book_id>", methods=["POST"])
@login_required
def request_book(book_id):
    book = db.session.get(Book, book_id)

    if current_user.id == book.owner_id:
        flash("You can't borrow your own book :)", "error")
        return redirect(url_for("books.book_details", book_id=book_id))

    if not book.availability:
        flash("Sorry, Currently Unavailable.", "error")
        return redirect(url_for("books.book_details", book_id=book_id))

    existing_request = BorrowRequest.query.filter_by(borrower_id=current_user.id, book_id=book_id).first()
    if existing_request:
        flash("You have already requested this book :)")
        return redirect(url_for("books.book_details", book_id=book_id))

    request_book = BorrowRequest(
        borrower_id=current_user.id,
        book_id=book_id
    )

    db.session.add(request_book)

    flash("Borrow request sent.", "success")

    requests = BorrowRequest.query.join(Book).filter(Book.owner_id == current_user.id).all()

    create_notification(
        owner_id=book.owner_id,
        message=f"{current_user.username} requested {book.title}",
        link=url_for("dashboard.dashboard", requests=requests, BorrowRequestStatus=BorrowRequestStatus)
    )

    msg = Message(
        sender_id=current_user.id,
        receiver_id=book.owner_id,
        book_id=book_id,
        content=f"Hi, I would like to borrow '{book.title}'."
    )

    db.session.add(msg)
    db.session.commit()

    return redirect(url_for("chats.chat", username=book.owner.username, book_id=book_id))


@books_bp.route("/book/search")
def search():
    query = request.args.get("query")

    if not query:
        return redirect(url_for("books.home"))

    books = Book.query.filter(Book.title.contains(query)).all()

    if not books:
        flash("No results found :(", "error")

    return render_template("book/home.html", books=books)


@books_bp.route("/api/unsplash/search")
@login_required
def unsplash_search():
    query = request.args.get("query", "")
    if not query:
        return jsonify([])

    access_key = current_app.config.get("UNSPLASH_ACCESS_KEY")
    if not access_key:
        return jsonify({"error": "Unsplash API key not configured"}), 400

    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 12, "orientation": "portrait"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        results = [
            {
                "id": r["id"],
                "url": r["urls"]["small"],
                "full": r["urls"]["regular"],
                "alt": r.get("alt_description", ""),
                "credit": r["user"]["name"]
            }
            for r in data.get("results", [])
        ]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
