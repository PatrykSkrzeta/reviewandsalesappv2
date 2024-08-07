from application import app
from flask import render_template, url_for, redirect,flash, get_flashed_messages, request, session
from application.models import Reviews, Sales, User
from application import db
from sqlalchemy import func
from datetime import datetime, timedelta
from application.forms import VerificationForm, LoginForm
import json
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
import pandas as pd
from werkzeug.utils import secure_filename
import os
from flask_mail import Mail, Message
import secrets


login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('review'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            verification_code = ''.join(secrets.choice('0123456789') for _ in range(6))
            user.verification_code = verification_code
            db.session.commit()

            msg = Message('Your verification code', sender='domo241@wp.pl', recipients=[user.email])
            msg.html = f"""
<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verification Code</title>
        <style>
            body {{
                background-color: #C2185B; /* Ciemny róż */
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                color: #4caf50; /* Zielony */
            }}
            .container {{
                max-width: 600px;
                margin: auto;
                background: #C2185B; /* Ciemny róż */
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            h1 {{
                font-size: 5rem;
            }}
            .header, .footer {{
                background-color: #C2185B; /* Ciemny róż */
                padding: 10px;
                color: #4caf50; /* Zielony */
                text-shadow: 1px 1px 1px black;
            }}
            .verification-code {{
                font-size: 4rem;
                color: white; /* Biały */
                font-weight: bold;
            }}
            p {{
                font-size: 3rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Saleboard</h1>
            </div>
            <p style="color: #4caf50;">Your 6-digit verification code:</p> <!-- Zielony tekst -->
            <p class="verification-code">{verification_code}</p>
            <p class="footer">Hallelujah!</p>
        </div>
    </body>
    </html>
                """
            try:
                mail.send(msg)
                session['verification_email'] = user.email
                return redirect(url_for('verify'))
            except Exception as e:
                flash(f'An error occurred while sending email: {str(e)}', 'danger')
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route("/verify", methods=['GET', 'POST'])
def verify():
    email = session.get('verification_email')

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    form = VerificationForm()
    if form.validate_on_submit():
        if user.verification_code == form.code.data:
            user.verification_code = None
            db.session.commit()
            login_user(user)
            session.pop('verification_email', None)
            flash('Verification successful. You are now logged in.', 'success')
            return redirect(url_for('review'))
        else:
            flash('Invalid verification code.', 'danger')
    
    return render_template('verify.html', title='Verify', form=form)


@app.route("/logout")
def logout():
    logout_user()
    session.pop('verification_email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/reviews')
@login_required
def review():
    name = request.args.get('name')
    sort_by = request.args.get('sort_by')

    query = Reviews.query

    if name:
        query = query.filter(Reviews.name.ilike(f'%{name}%'))

    if sort_by == 'rating_desc':
        query = query.order_by(
            Reviews.product_quality.desc(),
            Reviews.shipping_time.desc(),
            Reviews.shipping_quality.desc(),
            Reviews.contact_quality.desc()
        )
    elif sort_by == 'rating_asc':
        query = query.order_by(
            Reviews.product_quality.asc(),
            Reviews.shipping_time.asc(),
            Reviews.shipping_quality.asc(),
            Reviews.contact_quality.asc()
        )
    else:
        query = query.order_by(Reviews.name)

    data = query.all()

    for review in data:
        review.product_quality = '&#9733; ' * review.product_quality
        review.shipping_time = '&#9733; ' * review.shipping_time
        review.shipping_quality = '&#9733; ' * review.shipping_quality
        review.contact_quality = '&#9733; ' * review.contact_quality

    return render_template('review.html', data=data)

@app.route('/sales')
@login_required
def sales():
    category = request.args.get('category')
    date = request.args.get('date')
    product = request.args.get('product')
    query = Sales.query

    if category:
        query = query.filter(Sales.category.ilike(f'%{category}%'))
    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(Sales.date == search_date)
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('sales'))
    if product:
        query = query.filter(Sales.product.ilike(f'%{product}%'))

    data = query.all()

    return render_template('sales.html', data=data)

@app.route('/upload_review_csv', methods=['POST'])
@login_required
def upload_review_csv():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('review'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('review'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            df = pd.read_csv(file_path)
            df.to_sql('reviews', con=db.engine, if_exists='replace', index=False)
            flash('Data has been readen correctly!', 'success')
        except Exception as e:
            flash(f'ERROR: {str(e)}', 'danger')
        os.remove(file_path)
        return redirect(url_for('review'))

@app.route('/upload_sales_csv', methods=['POST'])
@login_required
def upload_sales_csv():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('sales'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('sales'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            df = pd.read_csv(file_path)
            df.to_sql('sales', con=db.engine, if_exists='replace', index=False)
            flash('Data has been readen correctly!', 'success')
        except Exception as e:
            flash(f'ERROR: {str(e)}', 'danger')
        os.remove(file_path)
        return redirect(url_for('sales'))


@app.route('/reviews/dashboard')
@login_required
def reviews_dashboard():
    avg_product_quality = db.session.query(func.avg(Reviews.product_quality)).scalar()
    avg_shipping_quality = db.session.query(func.avg(Reviews.shipping_quality)).scalar()
    avg_shipping_time = db.session.query(func.avg(Reviews.shipping_time)).scalar()
    avg_contact_quality = db.session.query(func.avg(Reviews.contact_quality)).scalar()


    chart_data = {
        'labels': ['Product Quality', 'Shipping Quality', 'Shipping Time', 'Contact with seller'],
        'data': [avg_product_quality, avg_shipping_quality, avg_shipping_time, avg_contact_quality]
    }

    return render_template('rdashboard.html', chart_data=chart_data)

@app.route('/sales/dashboard')
@login_required
def sales_dashboard():
    time_range = request.args.get('time-range', '1w') 


    reference_date = datetime(2023, 1, 1)

    try:
        if time_range == '1w':
            sales_data = Sales.query.filter(Sales.date >= reference_date - timedelta(weeks=1)).all()
        elif time_range == '1m':
            sales_data = Sales.query.filter(Sales.date >= reference_date - timedelta(weeks=4)).all()
        elif time_range == '6m':
            sales_data = Sales.query.filter(Sales.date >= reference_date - timedelta(weeks=26)).all()
        elif time_range == '1y':
            sales_data = Sales.query.filter(Sales.date >= reference_date - timedelta(weeks=52)).all()

        dates = [str(sale.date) for sale in sales_data]
        quantities = [sale.quantity for sale in sales_data]

        return render_template('sdashboard.html', dates=dates, quantities=quantities)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error_message="An error occurred while processing the request.")

if __name__ == '__main__':
    app.run(debug=True)
