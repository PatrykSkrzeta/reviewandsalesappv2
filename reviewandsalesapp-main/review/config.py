from application import app, db
from application.models import User
with app.app_context():
    # Tworzenie nowego użytkownika
    new_user = User(email='patryk.skrzeta@gmail.com')
    new_user.set_password('zaq1@WSX')
    
    # Dodanie użytkownika do sesji
    db.session.add(new_user)
    
    # Zapisanie sesji (commit)
    db.session.commit()