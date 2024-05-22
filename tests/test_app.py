import pytest
from app import create_app
from flask import g, session
from datetime import datetime, timedelta
import json

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
        return {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 15.0},
            "name": "Prague"
        }

    monkeypatch.setattr('app.routes.get_weather_data', mock_get_weather_data)

    rv = client.get('/api/current_weather?location=Prague')
    assert rv.status_code == 200

def test_weather_forecast(client, monkeypatch):
    def mock_get_forecast_data(location):
        return {
            "list": [
                {"dt": 1609459200, "main": {"temp": 10}, "weather": [{"description": "cloudy"}]}
            ]
        }

    monkeypatch.setattr('app.routes.get_forecast_data', mock_get_forecast_data)

    rv = client.get('/api/weather_forecast?location=Prague')
    assert rv.status_code == 200

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

    rv = client.post('/unsubscribe', follow_redirects=True)
    assert rv.status_code == 200
