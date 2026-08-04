from flask import Flask, render_template, request, redirect, url_for, flash

from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint

from forms import BookForm

from models import Book, BorrowRequest, Message, Notification

from extensions import db

GENRE_DATA = {

    "Fantasy": {

        "quote":
        "Magic is just reality waiting to be rewritten.",

        "mood":
        "Escape into worlds of dragons, kingdoms, and ancient prophecies.",

        "emoji":
        "🐉",

        "banner":
        "fantasy.jpg"
    },

    "Romance": {

        "quote":
        "Some stories stay with your heart forever.",

        "mood":
        "Soft emotions, unforgettable chemistry, and aching love stories.",

        "emoji":
        "💖",

        "banner":
        "romance.jpg"
    },

    "Thriller": {

        "quote":
        "Trust nobody. Question everything.",

        "mood":
        "Dark twists, dangerous secrets, and sleepless nights.",

        "emoji":
        "🔪",

        "banner":
        "thriller.jpg"
    },

    "Horror": {

        "quote":
        "Not every shadow is empty.",

        "mood":
        "Disturbing tales that linger long after midnight.",

        "emoji":
        "👻",

        "banner":
        "horror.jpg"
    }
}

books_bp = Blueprint("books", __name__)

@books_bp.route("/")
def home():

    books = Book.query.all()
    return render_template("book/home.html", books=books)

@books_bp.route("/book/add", methods=["GET", "POST"])
@login_required
def add_book():
    form = BookForm()


    if form.validate_on_submit():

        new_book = Book(
            title = form.title.data,
            author = form.author.data,
            genre = form.genre.data,
            description = form.description.data,
            image = form.image.data,
            rating = form.rating.data,
            user_id = current_user.id
        )
        
        db.session.add(new_book)
        db.session.commit()

        flash(
            "Book added successfully!",
            "success"
        )
        
        return redirect(url_for("books.home"))

    return render_template("book/addbook.html", form=form)

@books_bp.route("/book/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book.user_id != current_user.id:
        flash(
            "Can't delete book that doesn't belong to you",
            "error"
        )
        return redirect(url_for("books.home"))

    if book:
        db.session.delete(book)
        db.session.commit()

        flash(
            "Book deleted.",
            "success"
        )

    return redirect(url_for("books.home"))  

@books_bp.route("/book/edit/<int:book_id>", methods = ["GET", "POST"])
@login_required
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    if book.user_id != current_user.id:
        return redirect(url_for("books.home"))
    
    form = BookForm(obj = book)

    if request.method == "POST":
        
        book.title = form.title.data
        book.author = form.author.data
        book.genre = form.genre.data
        book.description = form.description.data
        book.image = form.image.data
        book.rating = form.rating.data

        db.session.commit()

        flash(
            "Book updated successfully!",
            "success"
        )

        return redirect(url_for("books.home"))
    
    return render_template("book/editbook.html", form=form)

@books_bp.route("/book/genre/<genre>")
def books_genre(genre):
    '''filter_by: 
    ANY column
    can return many objects
    more flexible
    '''
    books = Book.query.filter_by(genre = genre).all()

    genre_info = GENRE_DATA.get(genre)

    return render_template("book/genre.html", books = books, genre=genre, genre_info=genre_info)

@books_bp.route("/book/<int:book_id>")
def book_details(book_id):

    book = db.session.get(Book, book_id)

    return render_template("book/book.html", book = book)

@books_bp.route("/book/request/<int:book_id>", methods=["POST"])
@login_required
def request_book(book_id):

    book = db.session.get(Book, book_id)

    if current_user.id == book.user_id:
        flash(
            "You can't borrow your own book :)",
            "error"
        )
        return redirect(url_for("books.book_details"), book_id=book_id)

    if not book.availability:
        flash(
            "Sorry, Currently Unavailable.",
            "error"
        )
        return redirect(url_for("books.book_details"), book_id=book_id)
    
    existing_request = BorrowRequest.query.filter_by(borrower_id=current_user.id, book_id=book_id).first()
    if existing_request:
        flash(
            "You have already requested this book :)"
        )
        return redirect(url_for("books.book_details"), book_id=book_id)

    request_book = BorrowRequest(
        borrower_id = current_user.id,
        book_id = book_id
    )

    db.session.add(request_book)

    flash(
        "Borrow request sent.",
        "success"
    )

    requests = BorrowRequest.query.join(Book).filter(Book.user_id == current_user.id).all()
    notification = Notification(
        user_id = book.user_id,
        notif = f"{current_user.username} requested {book.title}",
        link = url_for("dashboard.dashboard", requests=requests)
    )

    db.session.add(notification)


    msg = Message(
        sender_id = current_user.id,
        receiver_id = book.user_id,
        book_id = book_id,
        content = f"Hi, I would like to borrow '{book.title}'."
    )

    db.session.add(msg)

    db.session.commit()

    return redirect(url_for("chats.chat", username = book.user.username, book_id=book_id))

@books_bp.route("/book/search")
def search():
    
    query = request.args.get("query")

    if not query:

        return redirect(url_for("books.home"))

    books = Book.query.filter(Book.title.contains(query)).all()

    if not books:
        flash(
            "No results found :(",
            "error"
        )

    return render_template("book/home.html", books=books)
