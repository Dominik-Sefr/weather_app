import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    WEATHER_API_KEY = '0ce37bdb01dd222e889fd9c4e64d1064'
    WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5'
    WEATHER_HISTORY_URL = 'http://history.openweathermap.org/data/2.5/history/city'

class TestConfig(Config):
    TESTING = True
    WEATHER_API_KEY = 'test_api_key'
