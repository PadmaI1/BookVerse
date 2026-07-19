from datetime import datetime

from flask_login import UserMixin

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from sqlalchemy import (
    String,
    Float,
    Numeric,
    DateTime
)

from extensions import (
    db,
    login_manager
)

from enum import Enum

from decimal import Decimal

# UserMixin provide: is_authenticated,is_active,get_id()..Flask-login requires these
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    city: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(default=False)
    password: Mapped[str] = mapped_column(String(200))
    profile_pic: Mapped[str] = mapped_column(String(500), nullable=False,default="default.jpg")
    about: Mapped[str] = mapped_column(String(500), nullable=True, default="")

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

    books = db.relationship("Book", backref="owner", cascade = "all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade = "all, delete-orphan")

'''
But when you inherit from db.Model:

SQLAlchemy now understands:

This is a database table.
Generate SQL for it.
Allow queries.
Allow inserts.
Allow updates.

Without db.Model, SQLAlchemy wouldn't know what to do with the class.
'''
class Book(db.Model):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(200))
    genre: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1000))
    availability: Mapped[bool] = mapped_column(default=True)
    security_deposit: Mapped[Decimal] = mapped_column(Numeric(10,2))
    image: Mapped[str] = mapped_column(String(500))
    rating: Mapped[float] = mapped_column(Float)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))

class BorrowRequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    RETURNED = "returned"
    REJECTED = "rejected"

class BorrowRequest(db.Model):
    __tablename__ = "borrow_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    borrower_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(db.ForeignKey("books.id"))
    status: Mapped[BorrowRequestStatus] = mapped_column(db.Enum(BorrowRequestStatus), default=BorrowRequestStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    '''
    book = db.relationship("Book")
    creates:
    request.book
    '''
    # RELATIONSHIPS
    book = db.relationship("Book")
    borrower = db.relationship("User",foreign_keys=[borrower_id],backref=db.backref("borrow_requests", cascade="all, delete-orphan"))

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
    notif: Mapped[str] = mapped_column(String(300))
    read: Mapped[bool] = mapped_column(default=False)
    link: Mapped[str] = mapped_column(String(300))
    timestamp: Mapped[datetime] = mapped_column(default = datetime.utcnow)

'''
Borrower requests book
          │
          ▼
Owner accepts request
          │
          ▼
Create Payment row in database (Status = PENDING)
          │
          ▼
Backend creates Razorpay Order
          │
          ▼
Save Razorpay Order ID
          │
          ▼
Return Order ID to frontend
          │
          ▼
Frontend opens Razorpay Checkout
          │
          ▼
User pays
          │
          ▼
Razorpay returns payment_id + signature
          │
          ▼
Frontend sends ONLY payment_id, order_id and signature
          │
          ▼
Backend verifies signature
          │
          ▼
Update Payment Status = SUCCESSFUL
          │
          ▼
Book can now be handed over
'''

class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentType(Enum):
    SECURITY_DEPOSIT = "security_deposit"
    SUBSCRIPTION = "subscription"
    REFUND = "refund"


class Payment(db.Model):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    borrower_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(db.ForeignKey("books.id"), nullable=False)
    borrow_request_id: Mapped[int] = mapped_column(db.ForeignKey("borrow_requests.id"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2),nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_type: Mapped[PaymentType] = mapped_column(db.Enum(PaymentType), nullable=False)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255),unique=True,nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255),unique=True,nullable=True)
    razorpay_refund_id: Mapped[str | None] = mapped_column(String(255),unique=True,nullable=True)
    payment_signature: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)
    original_payment_id: Mapped[int | None] = mapped_column(db.ForeignKey("payments.id"), nullable=True)
    borrower = db.relationship("User", foreign_keys=[borrower_id], backref=db.backref("payments_made", cascade="all, delete-orphan"))
    owner = db.relationship("User", foreign_keys=[owner_id], backref=db.backref("payments_received", cascade="all, delete-orphan"))
    book = db.relationship("Book", backref="payments")
    borrow_request = db.relationship("BorrowRequest", backref="payments")

    '''
"Flask-Login,
use THIS function later
to load users."
'''
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
