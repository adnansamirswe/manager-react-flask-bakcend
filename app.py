import os
from flask import Flask, jsonify
from flask_cors import CORS
from google.cloud import firestore
from google.oauth2 import service_account
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/check-expiry/*": {"origins": "*"}})

TELEGRAM_BOT_TOKEN = '6459343532:AAEukUlQbdvgg5eHgIOduSdgtkzfv0L1pMo'
TELEGRAM_CHAT_ID = '6012569599'

# Load credentials from environment variables
credentials_dict = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),  # Convert newline characters
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL')}",
    "universe_domain": "googleapis.com"
}

# Initialize Firestore client with credentials
credentials = service_account.Credentials.from_service_account_info(credentials_dict)
db = firestore.Client(credentials=credentials, project=credentials_dict['project_id'])

def send_telegram_message(message):
    """Send a message via the Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message")

def check_for_expired_users():
    """Check for expired users and notify via Telegram if any are found."""
    users_ref = db.collection('users')
    users = [doc.to_dict() for doc in users_ref.stream()]
    today = datetime.now().date()

    expired_users = []
    for user in users:
        expiry_date = datetime.strptime(user['expiry_date'], "%Y-%m-%d").date()
        if expiry_date < today:
            expired_users.append(user)
            send_telegram_message(f"User {user['username']} on server {user['servername']} has expired. Please take action.")

    return expired_users

@app.route('/check-expiry', methods=['GET'])
def check_expiry():
    """Endpoint to manually trigger expiry check."""
    expired_users = check_for_expired_users()
    return jsonify({"expired_users": expired_users}), 200

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
