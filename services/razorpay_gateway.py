import razorpay

from flask import current_app, abort, url_for

from flask_login import current_user

from extensions import db

from models import Book, BorrowRequest, BorrowRequestStatus, Payment, PaymentStatus, PaymentType

from razorpay.errors import SignatureVerificationError

from notification_service import create_notification

def get_razorpay_client():
    return razorpay.Client(
        auth=(current_app.config["RAZORPAY_KEY_ID"], current_app.config["RAZORPAY_KEY_SECRET"])
    )

def create_order(borrow_request_id:int, borrower_id:int):
    borrow_request = BorrowRequest.query.get(borrow_request_id)

    if not borrow_request:
        raise ValueError("Borrow request not found")

    if borrow_request.status != BorrowRequestStatus.APPROVED:
        raise ValueError("Payment is allowed only after the request is approved.")

    book = borrow_request.book

    if not book:
        raise ValueError("book not found.")
    
    if book.owner_id == borrower_id:
        raise ValueError("Owner cannot borrow their own book")    

    
    existing_payment = Payment.query.filter(
        Payment.book_id == book.id,
        Payment.borrower_id == borrower_id,
        Payment.payment_type == PaymentType.SECURITY_DEPOSIT,
        Payment.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.SUCCESSFUL])
    ).first()

    if existing_payment:
        raise ValueError("A security deposit payment already exists for this borrow request.")
    
    client = get_razorpay_client()

    amount = book.security_deposit * 100  # Convert to paise

    '''
    BookVerse
        │
        ▼
    Razorpay SDK
        │
        ▼
    HTTPS API Request
        │
        ▼
    Razorpay Server
        │
        ▼
    Creates Order
        │
        ▼
    Returns JSON
        │
        ▼
    Python Dictionary
    '''

    razorpay_order = client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "receipt": f"borrow_request_{borrow_request.id}",
        }
    )
    
    payment = Payment(
    borrower_id=borrower_id,
    owner_id=book.owner_id,
    book_id=book.id,
    borrow_request_id=borrow_request.id,
    amount_paid=book.security_deposit,
    payment_status=PaymentStatus.PENDING,
    payment_type=PaymentType.SECURITY_DEPOSIT,
    razorpay_order_id=razorpay_order["id"]
    )

    db.session.add(payment)
    db.session.commit()

    return {
        "order_id": razorpay_order["id"],
        "amount": amount,
        "currency": "INR",
        "key": current_app.config["RAZORPAY_KEY_ID"]
    }

def verify_payment(razorpay_order_id,razorpay_payment_id,razorpay_signature):
    client = get_razorpay_client()

    payment_data = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }

    try:
        client.utility.verify_payment_signature(payment_data)
    except SignatureVerificationError:
        raise ValueError("Payment signature verification failed.")
    
    payment = Payment.query.filter_by(razorpay_order_id=razorpay_order_id).first()

    if not payment:
        raise ValueError("Payment record not found.")

    mark_payment_successful(
        payment=payment,
        razorpay_payment_id=razorpay_payment_id,
        payment_signature=razorpay_signature
    )

    return {
        "message": "Payment verified successfully."
    }

def refund(borrow_request_id):

    payment = Payment.query.filter_by(borrow_request_id=borrow_request_id, payment_type=PaymentType.SECURITY_DEPOSIT, payment_status=PaymentStatus.SUCCESSFUL).first()

    if not payment:
        raise ValueError("Security deposit not found.")
    
    existing_refund = Payment.query.filter_by(original_payment_id=payment.id, payment_type=PaymentType.REFUND).first()

    if existing_refund:
        raise ValueError("Security deposit already refunded.")
    
    borrow_request = BorrowRequest.query.get_or_404(borrow_request_id)

    if borrow_request.book.owner_id != current_user.id:
        abort(403, description="You are not authorized to refund this security deposit.")
    
    client = get_razorpay_client()

    refund = client.payment.refund(
        payment.razorpay_payment_id,
        {
            "amount": int(payment.amount_paid * 100)  # Convert to paise
        }
    )

    borrow_request.status = BorrowRequestStatus.RETURNED

    payment.book.availability = True  # Mark the book as available again after refund

    refund_payment = Payment(
        borrower_id=payment.borrower_id,
        owner_id=payment.owner_id,
        book_id=payment.book_id,
        borrow_request_id=payment.borrow_request_id,
        amount_paid=payment.amount_paid,
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_type=PaymentType.REFUND,
        razorpay_refund_id=refund["id"],
        original_payment_id=payment.id
    )

    db.session.add(refund_payment)

    create_notification(
        user_id=payment.borrower_id,
        message=(
            f"Your security deposit of ₹{payment.amount_paid} "
            f'for "{payment.book.title}" has been refunded successfully.'
        ),
        link=url_for("borrow_requests.my_borrow_requests")
    )

    db.session.commit()

    return {
        "message": "Security deposit refunded successfully."
    }

def mark_payment_successful(payment: Payment, razorpay_payment_id: str, razorpay_signature: str| None = None):

    if payment.payment_status == PaymentStatus.SUCCESSFUL:
        return
    
    payment.payment_status = PaymentStatus.SUCCESSFUL
    payment.razorpay_payment_id = razorpay_payment_id
    payment.payment_signature = razorpay_signature
    payment.book.availability = False  # Mark the book as unavailable after successful payment
    payment.borrow_request.status = BorrowRequestStatus.ACTIVE

    create_notification(user_id=payment.owner_id,
                        message=f"{payment.borrower.username} has paid the security deposit for '{payment.book.title}'.",
                        link=url_for("dashboard.dashboard"))

    db.session.commit()