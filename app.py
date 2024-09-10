from flask import Flask, jsonify
from flask_cors import CORS
from google.cloud import firestore
from google.oauth2 import service_account
import requests
from datetime import datetime
import json

app = Flask(__name__)
CORS(app, resources={r"/check-expiry/*": {"origins": "*"}})

TELEGRAM_BOT_TOKEN = '6459343532:AAEukUlQbdvgg5eHgIOduSdgtkzfv0L1pMo'
TELEGRAM_CHAT_ID = '6012569599'

# Load credentials from firebase.json
with open('firebase.json') as f:
    credentials_dict = json.load(f)

credentials = service_account.Credentials.from_service_account_info(credentials_dict)

# Initialize Firestore client with credentials
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
