# author: Saif ali Karedia

import os


class Config:
    # SECRET_KEY = os.environ.get('SESSION_SECRET_KEY')
    SECRET_KEY = "Thisismyseeecreetttkeeeeyyy"  # secret key to handle session
    EMAIL = False  # set email as True to send emails from the application.

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    POSTGRES_PASSWORD = 'Qwerty8520$.'
    SQLALCHEMY_DATABASE_URI = 'postgresql://sk186170:' + POSTGRES_PASSWORD + '@localhost/Sims_Database'

    def __init__(self):
        pass

    DEBUG = True  # set debug as true when in development mode


class TestingConfig(Config):
    def __init__(self):
        pass

    TESTING = True  # set testing as true when in testing mode


class ProductionConfig(Config):
    POSTGRES_PASSWORD = 'aster4data'
    SQLALCHEMY_DATABASE_URI = 'postgresql://sims:' + POSTGRES_PASSWORD + '@localhost/Sims_Database'

    def __init__(self):
        pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
    'production': ProductionConfig
}
