from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/users/*": {"origins": "https://bdix-manager.web.app"}})

TELEGRAM_BOT_TOKEN = '6459343532:AAEukUlQbdvgg5eHgIOduSdgtkzfv0L1pMo'
TELEGRAM_CHAT_ID = '6012569599'

# Load users from a JSON file
def load_users():
    try:
        with open('users.json', 'r') as file:
            content = file.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Error: The users.json file contains invalid JSON.")
        return []

# Save users to a JSON file
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

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
    users = load_users()
    today = datetime.now().date()

    expired_users = []
    for user in users:
        expiry_date = datetime.strptime(user['expiry_date'], "%Y-%m-%d").date()
        if expiry_date < today:
            expired_users.append(user)
            # Send a Telegram message for each expired user
            send_telegram_message(f"User {user['username']} on server {user['servername']} has expired. please take action.")

    return expired_users

@app.route('/users', methods=['GET'])
def get_users():
    users = load_users()
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    new_user = request.json
    users = load_users()

    # Add a unique user_id
    new_user['user_id'] = len(users) + 1
    users.append(new_user)
    save_users(users)
    return jsonify({'message': 'User added successfully'}), 201

@app.route('/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    users = load_users()
    updated_data = request.json

    for user in users:
        if user['user_id'] == user_id:
            user.update(updated_data)
            save_users(users)
            return jsonify({"message": "User updated successfully"}), 200

    return jsonify({"message": "User not found"}), 404

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    users = load_users()
    users = [user for user in users if user['user_id'] != user_id]
    save_users(users)
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/check-expiry', methods=['GET'])
def check_expiry():
    """Endpoint to manually trigger expiry check."""
    expired_users = check_for_expired_users()
    return jsonify({"expired_users": expired_users}), 200

if __name__ == '__main__':
    app.run(debug=True)
