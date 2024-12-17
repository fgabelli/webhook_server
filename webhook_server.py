from flask import Flask, request, jsonify
import stripe
import json
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

app = Flask(__name__)

# Chiave segreta del webhook
endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")

# Percorso al file delle credenziali
CREDENTIALS_FILE = "user_credentials.json"

def load_credentials():
    with open(CREDENTIALS_FILE, 'r') as file:
        return json.load(file)

def save_credentials(credentials):
    with open(CREDENTIALS_FILE, 'w') as file:
        json.dump(credentials, file, indent=4)

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify(success=False), 400

    # Evento: pagamento completato
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session["customer_details"]["email"]

        # Aggiorna lo stato premium
        credentials = load_credentials()
        for username, user_data in credentials["usernames"].items():
            if user_data["email"] == customer_email:
                user_data["premium"] = True
                save_credentials(credentials)
                print(f"Utente {username} aggiornato a Premium.")
    return jsonify(success=True), 200

if __name__ == "__main__":
    app.run(port=5000)
