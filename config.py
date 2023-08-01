from os import environ

from dotenv import load_dotenv


# disable this in production
# load_dotenv()

class Config:
    # general settings
    SECRET_KEY = environ.get('FLASK_SECRET_KEY')

    # database
    SQLALCHEMY_DATABASE_URI = environ.get('FLASK_SQLALCHEMY_DATABASE_URI') # should be of str type
    # SQLALCHEMY_DATABASE_URI = True if environ.get('FLASK_SQLALCHEMY_DATABASE_URI') == 'True' else False
    FLASK_SQLALCHEMY_TRACK_MODIFICATIONS = environ.get('FLASK_SQLALCHEMY_TRACK_MODIFICATIONS')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass

class TestingConfig(Config):
    pass
