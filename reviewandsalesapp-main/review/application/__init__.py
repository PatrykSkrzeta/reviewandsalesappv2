from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = 'VFDVDFVFDVDFVFDVDFVFDVFDVDFVDFVDF'

app.config['MAIL_SERVER'] = 'smtp.wp.pl'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'domo241@wp.pl'
app.config['MAIL_PASSWORD'] = '' #nope

mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
app.config['SECRET_KEY'] = "JLKJJJO3IURYoiouolnojojouuoo=5y9y9youjuy952oohhbafdnoglhoho"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviewsDB.db'

db = SQLAlchemy(app)


from application import routes