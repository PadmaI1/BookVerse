from datetime import datetime

from flask_login import UserMixin

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from sqlalchemy import (
    String,
    Float
)

from extensions import (
    db,
    login_manager
)

# UserMixin provide: is_authenticated,is_active,get_id()..Flask-login requires these
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    city: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(200))
    profile_pic: Mapped[str] = mapped_column(String(500), nullable=False,default="default.jpg")

    #Relationship
    '''relationship() creates:
                    user.books,
                    book.user(backref="user")
                    
WITHOUT relationship()

You would manually query every time.

❌ Without relationship
books = Book.query.filter_by(
    user_id=user.id
).all()
✔ With relationship
user.books

MUCH cleaner.'''

    books = db.relationship("Book", backref="user", cascade = "all, delete-orphan")
    borrow_requests = db.relationship("BorrowRequest", backref='user', cascade = "all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade = "all, delete-orphan")

class Book(db.Model):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1000))
    availability: Mapped[bool] = mapped_column(default=True)
    image: Mapped[str] = mapped_column(String(500))
    rating: Mapped[float] = mapped_column(Float)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))

class BorrowRequest(db.Model):
    __tablename__ = "borrow_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    borrower_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(db.ForeignKey("books.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")

    '''
    book = db.relationship("Book")
    creates:
    request.book
    '''
    # RELATIONSHIPS
    book = db.relationship("Book")

class Message(db.Model):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    receiver_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    book_id: Mapped[int] = mapped_column(db.ForeignKey("books.id"))
    content: Mapped[str] = mapped_column(String(500))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    #RELATIONSHIPS
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    book = db.relationship("Book", foreign_keys=[book_id])

class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    notif: Mapped[dict] = mapped_column(String(300))
    read: Mapped[bool] = mapped_column(default=False)
    link: Mapped[str] = mapped_column(String(300))
    timestamp: Mapped[datetime] = mapped_column(default = datetime.utcnow)


    '''
"Flask-Login,
use THIS function later
to load users."
'''
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
