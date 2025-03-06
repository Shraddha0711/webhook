# https://docs.stripe.com/webhooks/quickstart
# https://docs.stripe.com/webhooks

from fastapi import Request, FastAPI, HTTPException
import stripe
from firebase_admin import credentials, firestore, initialize_app
import os
from pprint import pprint

# Initialize Firebase
cred_path = os.getenv("CRED_PATH")
cred = credentials.Certificate(cred_path)
initialize_app(cred)
db = firestore.client()

app=FastAPI()

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = 'whsec_dbc51a61bed928be0a6d60efce987c73198e5a18a72eba8d32b398373e47796a'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        session = event['data']['object']
        handle_checkout_session(session)

    return {"status": "success"}

def handle_checkout_session(session):
    # Fulfill the purchase
    customer_email = session.get('customer_email')
    pprint(session)
    # product_name = session['display_items'][0]['custom']['name']
    amount_total = session['amount_received']
    product_name = 'Connect Package'
    receipt_email=session['receipt_email']


    # Example: Update Firestore with the transaction
    transaction_data = {
        'email': receipt_email,
        'product': product_name,
        'amount': amount_total,
        'timestamp': firestore.SERVER_TIMESTAMP,
    }
    db.collection('transactions').add(transaction_data)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
