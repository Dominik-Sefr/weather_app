import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

DATA_DIR = 'data'

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
FAVORITES_FILE = os.path.join(DATA_DIR, 'favorites.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')

# Initialize JSON files if they don't exist or are empty
def initialize_json_file(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, 'w') as file:
            json.dump({}, file)

initialize_json_file(USERS_FILE)
initialize_json_file(FAVORITES_FILE)
initialize_json_file(HISTORY_FILE)

def read_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        return {}
    except json.JSONDecodeError:
        return {}

def write_json_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_subscribed=False):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_subscribed = is_subscribed

    @staticmethod
    def get(user_id):
        users = read_json_file(USERS_FILE)
        user_data = users.get(str(user_id))
        if user_data:
            return User(user_id, user_data['username'], user_data['email'], user_data['password_hash'], user_data.get('is_subscribed', False))
        return None

    @staticmethod
    def get_by_email(email):
        users = read_json_file(USERS_FILE)
        for user_id, user_data in users.items():
            if user_data['email'] == email:
                return User(user_id, user_data['username'], user_data['email'], user_data['password_hash'], user_data.get('is_subscribed', False))
        return None

    @staticmethod
    def create(username, email, password):
        users = read_json_file(USERS_FILE)
        user_id = len(users) + 1
        password_hash = generate_password_hash(password)
        users[user_id] = {'username': username, 'email': email, 'password_hash': password_hash, 'is_subscribed': False}
        write_json_file(USERS_FILE, users)
        return User(user_id, username, email, password_hash)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def subscribe(self):
        users = read_json_file(USERS_FILE)
        users[str(self.id)]['is_subscribed'] = True
        write_json_file(USERS_FILE, users)

    def unsubscribe(self):
        users = read_json_file(USERS_FILE)
        users[str(self.id)]['is_subscribed'] = False
        write_json_file(USERS_FILE, users)

class FavoriteLocation:
    def __init__(self, user_id, city, country):
        self.user_id = user_id
        self.city = city
        self.country = country

    @staticmethod
    def get_by_user_id(user_id):
        favorites = read_json_file(FAVORITES_FILE)
        return favorites.get(str(user_id), [])

    @staticmethod
    def add(user_id, city, country):
        favorites = read_json_file(FAVORITES_FILE)
        user_favorites = favorites.get(str(user_id), [])
        user_favorites.append({'city': city, 'country': country})
        favorites[str(user_id)] = user_favorites
        write_json_file(FAVORITES_FILE, favorites)

    @staticmethod
    def delete(user_id, city, country):
        favorites = read_json_file(FAVORITES_FILE)
        user_favorites = favorites.get(str(user_id), [])
        user_favorites = [f for f in user_favorites if not (f['city'] == city and f['country'] == country)]
        favorites[str(user_id)] = user_favorites
        write_json_file(FAVORITES_FILE, favorites)

class WeatherHistory:
    def __init__(self, user_id, city, country, temperature, description, date):
        self.user_id = user_id
        self.city = city
        self.country = country
        self.temperature = temperature
        self.description = description
        self.date = date

    @staticmethod
    def get_by_user_id(user_id):
        history = read_json_file(HISTORY_FILE)
        user_history = history.get(str(user_id), [])
        # Convert date strings back to datetime objects
        for record in user_history:
            record['date'] = datetime.strptime(record['date'], '%Y-%m-%d %H:%M:%S')
        return user_history

    @staticmethod
    def add(user_id, city, country, temperature, description, date):
        history = read_json_file(HISTORY_FILE)
        user_history = history.get(str(user_id), [])
        # Convert datetime object to string before saving
        user_history.append({'city': city, 'country': country, 'temperature': temperature, 'description': description, 'date': date.strftime('%Y-%m-%d %H:%M:%S')})
        history[str(user_id)] = user_history
        write_json_file(HISTORY_FILE, history)
