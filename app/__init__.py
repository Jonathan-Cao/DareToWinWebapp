from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

import pyrebase

firebaseConfig = {
    "apiKey": "AIzaSyAQH6omlw0XpDKIle7mMmGXJgI6h6chKyw",
    "authDomain": "daretowin-d9c02.firebaseapp.com",
    "databaseURL": "https://daretowin-d9c02.firebaseio.com",
    "projectId": "daretowin-d9c02",
    "storageBucket": "daretowin-d9c02.appspot.com",
    "messagingSenderId": "48425414772",
    "appId": "1:48425414772:web:9bea54f2c1313bd32f2121",
    "measurementId": "G-889YJM5S1L"
}
firebase = pyrebase.initialize_app(firebaseConfig)#initialise firebase
fbStorage = firebase.storage()#initialise storage

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

from app import routes, models, errors

#To log errors by email, file, or heroku logs
def create_app(config_class = Config):
    if not app.debug and not app.testing: #Only when not running in debug mode
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='DareToWin Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
            
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/DareToWin.log', maxBytes=10240,
                                               backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('DareToWin startup')
    return app
