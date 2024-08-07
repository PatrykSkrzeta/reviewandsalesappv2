from application import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    verification_code = db.Column(db.String(6), nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Reviews(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    product_quality = db.Column(db.Integer)
    shipping_time = db.Column(db.Integer)
    shipping_quality = db.Column(db.Integer)
    contact_quality = db.Column(db.Integer)

class Sales(db.Model):
    date = db.Column(db.DateTime, primary_key=True)
    product = db.Column(db.String(255))
    category = db.Column(db.String(255))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    revenue = db.Column(db.Integer)
