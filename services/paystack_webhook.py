import hashlib
import hmac
import json

from django.conf import settings
from django.db import transaction as db_transaction
from django.http import HttpResponse, JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def paystack_webhook(request):
    # Step 1: Validate Paystack Signature
    paystack_signature = request.headers.get("X-Paystack-Signature")
    if not paystack_signature:
        return JsonResponse({"error": "Missing signature"}, status=400)

    payload = request.body
    computed_signature = hmac.new(
        key=settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha512,
    ).hexdigest()

    if not constant_time_compare(computed_signature, paystack_signature):
        return JsonResponse({"error": "Invalid signature"}, status=400)

    # Step 2: Process the Event
    data = json.loads(payload)
    event = data.get("event")
    event_data = data.get("data", {})
    metadata = event_data.get("metadata", {})

    transaction_id = metadata.get("transaction_id")
    # user_id = metadata.get('user_id')

    if not transaction_id:
        return JsonResponse({"error": "Invalid metadata"}, status=400)

    transaction = ... # retrieve transaction from database
    if not transaction:
        return JsonResponse({"error": "Transaction not found"}, status=404)

    # Step 3: Handle Charge Success and Failure
    if event == "charge.success":
        with db_transaction.atomic():
            transaction.status = "successful"
            transaction.save()

            # Update user's wallet balance if it's a deposit
            if transaction.transaction_type == "payment":
                wallet = transaction.recipient.wallet
                wallet.balance += transaction.amount
                wallet.save()

    elif event == "charge.failed":
        # Mark transaction as failed
        transaction.status = "failed"
        transaction.save()

    return HttpResponse(status=200)
