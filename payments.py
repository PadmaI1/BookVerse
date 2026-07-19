
from flask_login import (
    login_required,
    current_user
)

from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash, current_app

from services.razorpay_gateway import create_order, verify_payment, refund, mark_payment_successful

from models import BorrowRequest, BorrowRequestStatus, Payment, PaymentStatus, PaymentType

import razorpay

from razorpay.errors import SignatureVerificationError

from services.razorpay_gateway import get_razorpay_client


payments_bp = Blueprint("payments", __name__, url_prefix="/payments")

@payments_bp.route("/create-order", methods=["POST"])
@login_required
def create_payment_order():
    borrow_request_id = request.json.get("borrow_request_id")

    if not borrow_request_id:
        return jsonify({"error": "Boroow Request ID is required"}), 400
    
    payment_order = create_order(borrow_request_id, current_user.id)

    return jsonify(payment_order), 200

@payments_bp.route("/<int:borrow_request_id>")
@login_required
def payment_page(borrow_request_id):
    
    borrow_request = BorrowRequest.query.get_or_404(borrow_request_id)

    if borrow_request.borrower_id != current_user.id:
        abort(403, description="You are not authorized to view this payment page.")

    if borrow_request.status not in [
        BorrowRequestStatus.APPROVED,
        BorrowRequestStatus.ACTIVE,
        BorrowRequestStatus.RETURNED
    ]:
        flash(
            "Borrow Request is not approved.",
            "error"
        )

        return redirect(url_for("borrow_requests.my_borrow_requests", borrow_request_id=borrow_request.id))

    payment = Payment.query.filter_by(
        borrow_request_id=borrow_request.id,
        payment_type=PaymentType.SECURITY_DEPOSIT,
        payment_status=PaymentStatus.SUCCESSFUL
    ).first()

    return render_template(
        "payments.html",
        borrow_request=borrow_request,
        payment=payment
    )

@payments_bp.route("/verify", methods=["POST"])
@login_required
def verify():
    data = request.json

    result = verify_payment(
        razorpay_order_id=data.get("razorpay_order_id"),
        razorpay_payment_id=data.get("razorpay_payment_id"),
        razorpay_signature=data.get("razorpay_signature")
    )

    return jsonify(result), 200

@payments_bp.route("/confirm-return/<int:borrow_request_id>", methods=["POST"])
@login_required
def confirm_return(borrow_request_id):

    borrow_request = BorrowRequest.query.get_or_404(borrow_request_id)

    if borrow_request.book.owner_id != current_user.id:
        abort(403, description="You are not authorized to process this refund.")

    if borrow_request.status != BorrowRequestStatus.ACTIVE:
        flash(
            "Book is not currently borrowed. Refund cannot be processed.",
            "error"
        )
        return redirect(url_for("dashboard.dashboard"))
    
    try:

        refund(borrow_request.id)

        flash(
            "Security deposit refunded successfully.",
            "success"
        )

    except ValueError as e:
        flash(
            str(e),
            "error"
        )

    return redirect(url_for("dashboard.dashboard"))

@payments_bp.route("/webhook", methods=["POST"])
def webhook():

    
    body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature")

    client = get_razorpay_client()

    try:
        client.utility.verify_webhook_signature(
            body,
            signature,
            current_app.config["RAZORPAY_WEBHOOK_SECRET"]
        )
    except SignatureVerificationError:
        return jsonify({
            "error": "Invalid webhook signature."
        }), 403
    

    data = request.json

    if data["event"] != "payment.captured":
        return jsonify(
            {
                "message": "Ignored"
            }
        ), 200
    
    entity = data["payload"]["payment"]["entity"]

    payment = Payment.query.filter_by(razorpay_order_id = entity["order_id"]).first()

    if not payment:
        return jsonify(
            {
                "message": "Payment record not found."
            }
        ), 404
    
    mark_payment_successful(
        payment=payment,
        razorpay_payment_id=entity["id"]
    )

    return jsonify(
        {
            "message": "Webhook processed."
        }
    ), 200