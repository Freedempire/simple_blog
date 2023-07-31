from os import environ

from dotenv import load_dotenv


load_dotenv()

class Config:
    # general settings
    SECRET_KEY = environ.get('FLASK_SECRET_KEY')

    # database
    SQLALCHEMY_DATABASE_URI = environ.get('FLASK_SQLALCHEMY_DATABASE_URI') # should be of str type
    # SQLALCHEMY_DATABASE_URI = True if environ.get('FLASK_SQLALCHEMY_DATABASE_URI') == 'True' else False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass

class TestingConfig(Config):
    pass
