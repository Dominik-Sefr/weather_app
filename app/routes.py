from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for, flash
import requests
from flask_login import login_required, current_user
from app.models import FavoriteLocation, WeatherHistory, User
from config import Config
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/current_weather', methods=['GET'])
def current_weather():
    location = request.args.get('location')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if location:
        weather_data = get_weather_data(location=location)
    elif lat and lon:
        weather_data = get_weather_data(lat=lat, lon=lon)
    else:
        return jsonify({"error": "Location or coordinates are required"}), 400

    
    return jsonify(weather_data)

@bp.route('/api/weather_forecast', methods=['GET'])
def weather_forecast():
    location = request.args.get('location')
    forecast_data = get_forecast_data(location)
    return jsonify(forecast_data)

@bp.route('/favorites', methods=['GET', 'POST'])
@login_required
def favorites():
    if not current_user.is_subscribed:
        flash('You must be subscribed to access favorites.', 'warning')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        city = request.form['city']
        country = request.form['country']
        FavoriteLocation.add(current_user.id, city, country)
        flash('Favorite location added successfully!', 'success')

    favorites = FavoriteLocation.get_by_user_id(current_user.id)
    favorite_weather = []
    for favorite in favorites:
        weather_data = get_weather_data(f"{favorite['city']},{favorite['country']}")
        weather_history = get_weather_history(f"{favorite['city']},{favorite['country']}")
        favorite_weather.append({
            'city': favorite['city'],
            'country': favorite['country'],
            'weather': weather_data,
            'history': weather_history
        })

    return render_template('favorites.html', favorite_weather=favorite_weather)

@bp.route('/favorites/delete', methods=['POST'])
@login_required
def delete_favorite():
    city = request.form['city']
    country = request.form['country']
    FavoriteLocation.delete(current_user.id, city, country)
    flash('Favorite location deleted successfully!', 'success')
    return redirect(url_for('main.favorites'))

@bp.route('/history', methods=['GET'])
@login_required
def history():
    weather_history = WeatherHistory.get_by_user_id(current_user.id)
    return render_template('history.html', history=weather_history)

@bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    current_user.subscribe()
    flash('You have subscribed successfully!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    current_user.unsubscribe()
    flash('You have unsubscribed successfully!', 'success')
    return redirect(url_for('main.index'))

def get_weather_data(location=None, lat=None, lon=None):
    api_key = current_app.config['WEATHER_API_KEY']
    api_url = current_app.config['WEATHER_API_URL']
    
    
    
    params = {'appid': api_key, 'units': 'metric'}
    if location:
        params['q'] = location
    elif lat and lon:
        params['lat'] = lat
        params['lon'] = lon
    else:
        return {'error': 'Location or coordinates are required'}
    
    response = requests.get(f'{api_url}/weather', params=params)
    data = response.json()
    
    print("API Response Code:", response.status_code)
    
    if response.status_code != 200 or data.get('cod') != 200:
        return {'error': 'Invalid location or no data available'}
    
    if current_user.is_authenticated:
        city_name = data['name']
        country = data['sys']['country']
        temperature = data['main']['temp']
        description = data['weather'][0]['description']
        date = datetime.utcnow()
        WeatherHistory.add(current_user.id, city_name, country, temperature, description, date)
    
    return data

def get_forecast_data(location):
    api_key = current_app.config['WEATHER_API_KEY']
    api_url = current_app.config['WEATHER_API_URL']
    response = requests.get(f'{api_url}/forecast', params={'q': location, 'appid': api_key, 'units': 'metric'})
    return response.json()

def get_weather_data(location=None, lat=None, lon=None):
    api_key = current_app.config['WEATHER_API_KEY']
    api_url = current_app.config['WEATHER_API_URL']
    
    
    params = {'appid': api_key, 'units': 'metric'}
    if location:
        params['q'] = location
    elif lat and lon:
        params['lat'] = lat
        params['lon'] = lon
    else:
        return {'error': 'Location or coordinates are required'}
    
    response = requests.get(f'{api_url}/weather', params=params)
    data = response.json()
    
    # Debug output to console
    print("API Response Code:", response.status_code)
    
    if response.status_code != 200 or data.get('cod') != 200:
        return {'error': 'Invalid location or no data available'}
    
    if current_user.is_authenticated:
        city_name = data['name']
        country = data['sys']['country']
        temperature = data['main']['temp']
        description = data['weather'][0]['description']
        date = datetime.utcnow()
        WeatherHistory.add(current_user.id, city_name, country, temperature, description, date)
    
    return data

def get_weather_history(location):
    api_key = current_app.config['WEATHER_API_KEY']
    history_url = current_app.config['WEATHER_HISTORY_URL']
    
    # Get current time and ensure we are getting data for the same hour each day
    end_time = datetime.utcnow()
    
    # Get coordinates for the location
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
    geocode_params = {'q': location, 'appid': api_key}
    geocode_response = requests.get(geocode_url, params=geocode_params)
    geocode_data = geocode_response.json()
    
    if not geocode_data:
        return [{'dt': None, 'temp': None, 'weather': [{'description': 'No data available'}]}]

    lat = geocode_data[0].get('lat')
    lon = geocode_data[0].get('lon')
    
    if lat is None or lon is None:
        return [{'dt': None, 'temp': None, 'weather': [{'description': 'Invalid location'}]}]

    history_data = []
    for days_ago in range(1, 6):
        dt = end_time - timedelta(days=days_ago)
        timestamp = int(dt.timestamp())
        
        history_params = {
            'lat': lat,
            'lon': lon,
            'type': 'hour',
            'start': timestamp,
            'cnt': 1,
            'appid': api_key,
            'units': 'metric'
        }
        
        # Build the full URL with parameters
        request_url = requests.Request('GET', history_url, params=history_params).prepare().url
        
        # Debug output
        print(f"Requesting weather history for {location} from {timestamp}")
        print(f"URL: {request_url}")
        
        response = requests.get(request_url)
        
        print(f"API Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'list' in data:
                history_data.extend(data['list'])
    
    if not history_data:
        return [{'dt': None, 'temp': None, 'weather': [{'description': 'No historical data available'}]}]

    return history_data
