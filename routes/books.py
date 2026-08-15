from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app, abort

from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint

from forms import BookForm

from models import Book, Genre, User, BorrowRequest, BorrowRequestStatus, Message, Notification

from extensions import db

from sqlalchemy import or_

from services.notification_service import create_notification

import requests


books_bp = Blueprint("books", __name__)


def _genre_choices():
    return [(g.id, g.name) for g in Genre.query.order_by(Genre.name).all()]


HOME_SORTS = {
    "newest": Book.id.desc(),
    "rating": Book.rating.desc(),
    "deposit": Book.security_deposit.asc(),
}


def _render_home(query=None):
    """Render the discover page; any filter, sort or search switches it to a results grid."""
    genre_id = request.args.get("genre", type=int)
    city = request.args.get("city") or None
    max_deposit = request.args.get("max_deposit", type=int)
    available_only = request.args.get("available") == "1"
    sort = request.args.get("sort", "newest")
    if sort not in HOME_SORTS:
        sort = "newest"

    results = Book.query.join(User, Book.owner_id == User.id)
    if query:
        like = f"%{query}%"
        results = results.filter(or_(Book.title.ilike(like), Book.author.ilike(like)))
    if genre_id:
        results = results.filter(Book.genre_id == genre_id)
    if city:
        results = results.filter(User.city == city)
    if max_deposit:
        results = results.filter(Book.security_deposit <= max_deposit)
    if available_only:
        results = results.filter(Book.availability.is_(True))
    results = results.order_by(HOME_SORTS[sort], Book.id.desc()).all()

    is_filtered = bool(query or genre_id or city or max_deposit or available_only or sort != "newest")

    vibes = sorted(Genre.query.all(), key=lambda g: len(g.books), reverse=True)[:4]

    cities = [c for (c,) in db.session.query(User.city).join(Book, Book.owner_id == User.id).distinct().order_by(User.city)]

    return render_template(
        "book/home.html",
        books=Book.query.all(),
        results=results,
        is_filtered=is_filtered,
        cities=cities,
        vibes=vibes,
        search_query=query or "",
        active={"genre": genre_id, "city": city, "max_deposit": max_deposit, "available": available_only, "sort": sort},
    )


@books_bp.route("/")
def home():
    return _render_home()


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

    city = request.args.get("city") or None
    available_only = request.args.get("available") == "1"
    sort = request.args.get("sort", "rating")
    if sort not in HOME_SORTS:
        sort = "rating"

    shelf = Book.query.join(User, Book.owner_id == User.id).filter(Book.genre_id == genre.id)
    if city:
        shelf = shelf.filter(User.city == city)
    if available_only:
        shelf = shelf.filter(Book.availability.is_(True))
    shelf = shelf.order_by(HOME_SORTS[sort], Book.id.desc()).all()

    cities = [c for (c,) in db.session.query(User.city).join(Book, Book.owner_id == User.id).filter(Book.genre_id == genre.id).distinct().order_by(User.city)]

    # other genres, each with its top-rated book as a spotlight
    others = []
    for g in Genre.query.order_by(Genre.name).all():
        if g.id == genre.id or not g.books:
            continue
        others.append({"genre": g, "count": len(g.books), "spotlight": max(g.books, key=lambda b: (b.rating, b.id))})

    return render_template(
        "book/genre.html",
        genre=genre,
        books=shelf,
        total=len(genre.books),
        owner_count=len({b.owner_id for b in genre.books}),
        cities=cities,
        others=others,
        active={"city": city, "available": available_only, "sort": sort},
    )


@books_bp.route("/book/<int:book_id>")
def book_details(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)

    owner_books = Book.query.filter(Book.owner_id == book.owner_id, Book.id != book.id).order_by(Book.id.desc()).all()
    similar = Book.query.filter(Book.genre_id == book.genre_id, Book.owner_id != book.owner_id, Book.id != book.id).order_by(Book.rating.desc()).limit(4).all()

    my_request = None
    if current_user.is_authenticated:
        my_request = BorrowRequest.query.filter_by(borrower_id=current_user.id, book_id=book.id).order_by(BorrowRequest.id.desc()).first()

    return render_template(
        "book/book.html",
        book=book,
        owner_books=owner_books,
        similar=similar,
        my_request=my_request,
    )


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

    create_notification(
        user_id=book.owner_id,
        message=f"{current_user.username} requested {book.title}",
        link=url_for("dashboard.dashboard")
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

    if not query or not query.strip():
        return redirect(url_for("books.home"))

    return _render_home(query=query.strip())


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
