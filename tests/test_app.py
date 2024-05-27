import pytest
from app import create_app
from flask import g, session, current_app
from datetime import datetime, timedelta
import json
from unittest.mock import patch
from app.models import User, FavoriteLocation, WeatherHistory
from app.routes import get_weather_history, get_weather_data

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test'

    with app.test_client() as client:
        with app.app_context():
            yield client

def register(client, username, email, password):
    return client.post('/auth/register', data=dict(
        username=username,
        email=email,
        password=password,
        password2=password
    ), follow_redirects=True)

def login(client, email, password):
    return client.post('/auth/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200

def test_current_weather(client, monkeypatch):
    def mock_get_weather_data(location=None, lat=None, lon=None):
        if not location and not (lat and lon):
            return {"error": "Location or coordinates are required"}
        return {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15.0},
            "name": "Prague"
        }

    monkeypatch.setattr('app.routes.get_weather_data', mock_get_weather_data)

    # Test with location
    rv = client.get('/api/current_weather?location=Prague')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['weather'][0]['description'] == 'clear sky'
    assert json_data['main']['temp'] == 15.0

    # Test with coordinates
    rv = client.get('/api/current_weather?lat=50.0755&lon=14.4378')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['weather'][0]['description'] == 'clear sky'
    assert json_data['main']['temp'] == 15.0

    # Test without location or coordinates
    rv = client.get('/api/current_weather')
    assert rv.status_code == 400
    json_data = rv.get_json()
    assert json_data['error'] == "Location or coordinates are required"

def test_favorites(client, monkeypatch):
    register(client, 'testuser', 'test@example.com', 'testpassword')
    login(client, 'test@example.com', 'testpassword')

    def mock_get_weather_data(location=None, lat=None, lon=None):
        return {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15.0},
            "name": "Prague"
        }

    def mock_get_weather_history(location):
        return [
            {"dt": datetime(2021, 1, 1, 12, 0).timestamp(), "main": {"temp": 10.0}, "weather": [{"description": "cloudy"}]}
        ]

    monkeypatch.setattr('app.routes.get_weather_data', mock_get_weather_data)
    monkeypatch.setattr('app.routes.get_weather_history', mock_get_weather_history)

    rv = client.post('/favorites', data=dict(city='Prague', country='Czech Republic'), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/favorites', follow_redirects=True)
    assert rv.status_code == 200

def test_delete_favorite(client, monkeypatch):
    register(client, 'testuser', 'test@example.com', 'testpassword')
    login(client, 'test@example.com', 'testpassword')

    def mock_get_weather_data(location=None, lat=None, lon=None):
        return {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15.0},
            "name": "Prague"
        }

    monkeypatch.setattr('app.routes.get_weather_data', mock_get_weather_data)

    client.post('/favorites', data=dict(city='Prague', country='Czech Republic'), follow_redirects=True)
    rv = client.post('/favorites/delete', data=dict(city='Prague', country='Czech Republic'), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/favorites', follow_redirects=True)
    assert b'Prague' not in rv.data

def test_history(client, monkeypatch):
    register(client, 'testuser', 'test@example.com', 'testpassword')
    login(client, 'test@example.com', 'testpassword')

    def mock_get_weather_history(location):
        return [
            {"dt": datetime(2021, 1, 1, 12, 0).timestamp(), "main": {"temp": 10.0}, "weather": [{"description": "cloudy"}]}
        ]

    monkeypatch.setattr('app.routes.get_weather_history', mock_get_weather_history)

    rv = client.get('/history', follow_redirects=True)
    assert rv.status_code == 200

def test_subscribe_unsubscribe(client):
    register(client, 'testuser', 'test@example.com', 'testpassword')
    login(client, 'test@example.com', 'testpassword')

    rv = client.post('/subscribe', follow_redirects=True)
    assert rv.status_code == 200

    user = User.get_by_email('test@example.com')
    assert user.is_subscribed

    rv = client.post('/unsubscribe', follow_redirects=True)
    assert rv.status_code == 200

    user = User.get_by_email('test@example.com')

def test_user_model():
    user = User.create('testuser', 'test@example.com', 'testpassword')
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.check_password('testpassword')

    fetched_user = User.get_by_email('test@example.com')
    assert fetched_user is not None
    assert fetched_user.username == 'testuser'

    user.subscribe()
    assert User.get(user.id).is_subscribed
    user.unsubscribe()
    assert not User.get(user.id).is_subscribed

def test_favorite_location_model():
    user = User.create('testuser2', 'test2@example.com', 'testpassword')
    user_id = user.id

    FavoriteLocation.add(user_id, 'Paris', 'France')
    favorites = FavoriteLocation.get_by_user_id(user_id)
    assert len(favorites) == 1
    assert favorites[0]['city'] == 'Paris'
    assert favorites[0]['country'] == 'France'

    FavoriteLocation.delete(user_id, 'Paris', 'France')
    favorites = FavoriteLocation.get_by_user_id(user_id)
    assert len(favorites) == 0

def test_weather_history_model():
    user = User.create('testuser3', 'test3@example.com', 'testpassword')
    user_id = user.id

    WeatherHistory.add(user_id, 'Berlin', 'Germany', 20.0, 'sunny', datetime.utcnow())
    history = WeatherHistory.get_by_user_id(user_id)
    assert len(history) == 1
    assert history[0]['city'] == 'Berlin'
    assert history[0]['country'] == 'Germany'
    assert history[0]['temperature'] == 20.0
    assert history[0]['description'] == 'sunny'
    assert isinstance(history[0]['date'], datetime)

# Additional tests for get_weather_history function

def test_get_weather_history_success(client):
    location = 'Test Location'
    
    geocode_response = [{'lat': 10.0, 'lon': 20.0}]
    history_response = {
        'list': [{
            'dt': int((datetime.utcnow() - timedelta(days=1)).timestamp()),
            'main': {'temp': 25},
            'weather': [{'description': 'Clear sky'}]
        }]
    }
    
    with client.application.app_context():
        with patch('requests.get') as mock_get:
            # Mock the geocode response
            mock_get.side_effect = [
                MockResponse(geocode_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200)
            ]
            
            result = get_weather_history(location)

            assert len(result) > 0
            assert result[0]['dt'] is not None
            assert result[0]['main']['temp'] == 25
            assert result[0]['weather'][0]['description'] == 'Clear sky'

def test_get_weather_history_no_geocode_data(client):
    location = 'Invalid Location'
    
    with client.application.app_context():
        with patch('requests.get') as mock_get:
            # Mock the geocode response with no data
            mock_get.side_effect = [
                MockResponse([], 200)
            ]
            
            result = get_weather_history(location)

            assert result == [{'dt': None, 'temp': None, 'weather': [{'description': 'No data available'}]}]

def test_get_weather_history_invalid_location(client):
    location = 'Invalid Location'
    
    geocode_response = [{'lat': None, 'lon': None}]
    
    with client.application.app_context():
        with patch('requests.get') as mock_get:
            # Mock the geocode response with invalid data
            mock_get.side_effect = [
                MockResponse(geocode_response, 200)
            ]
            
            result = get_weather_history(location)

            assert result == [{'dt': None, 'temp': None, 'weather': [{'description': 'Invalid location'}]}]

def test_get_weather_history_no_history_data(client):
    location = 'Test Location'
    
    geocode_response = [{'lat': 10.0, 'lon': 20.0}]
    history_response = {}
    
    with client.application.app_context():
        with patch('requests.get') as mock_get:
            # Mock the geocode and history responses
            mock_get.side_effect = [
                MockResponse(geocode_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200),
                MockResponse(history_response, 200)
            ]
            
            result = get_weather_history(location)

            assert result == [{'dt': None, 'temp': None, 'weather': [{'description': 'No historical data available'}]}]

# Additional tests for get_weather_data function


def test_get_weather_data_no_location_or_coordinates(client):
    with client.application.app_context():
        result = get_weather_data()
        assert 'error' in result
        assert result['error'] == 'Location or coordinates are required'

def test_get_weather_data_invalid_location(client):
    location = 'InvalidLocation'
    
    weather_response = {'cod': '404', 'message': 'city not found'}
    
    with client.application.app_context():
        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(weather_response, 404)
            
            result = get_weather_data(location=location)
            
            assert 'error' in result
            assert result['error'] == 'Invalid location or no data available'

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data
