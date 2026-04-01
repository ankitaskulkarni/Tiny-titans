# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session handling
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timebank.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    hours = db.Column(db.Float, default=5.0)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'offer' or 'request'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # only for offers

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('User already exists. Try logging in.')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Try again.')
            return redirect(url_for('login'))
    return render_template('login.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    offers = Service.query.filter_by(user_id=user.id, type='offer').all()
    requests = Service.query.filter_by(user_id=user.id, type='request').all()
    return render_template('dashboard.html', username=session['username'], user=user, offers=offers, requests=requests)

# Offer a Service
@app.route('/offer', methods=['GET', 'POST'])
def offer():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
       service_name = request.form['service']
       category = request.form['category']
       user = User.query.filter_by(username=session['username']).first()
       service = Service(type='offer', user_id=user.id, service_name=service_name, category=category)
       db.session.add(service)
       db.session.commit()
       return redirect(url_for('dashboard'))
    return render_template('offer.html')

# Request a Service
@app.route('/request_service', methods=['GET', 'POST'])
def request_service():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        service_name = request.form['service']
        user = User.query.filter_by(username=session['username']).first()
        service = Service(type='request', user_id=user.id, service_name=service_name)
        db.session.add(service)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('request.html')

# View all Services
@app.route('/view_services')
def view_services():
    services = Service.query.all()
    return render_template('view_services.html', services=services)

# Exchange Time
@app.route('/exchange', methods=['GET', 'POST'])
def exchange():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        receiver_username = request.form['receiver']
        hours = float(request.form['hours'])

        sender = User.query.filter_by(username=session['username']).first()
        receiver = User.query.filter_by(username=receiver_username).first()

        if not receiver:
            return "Receiver not found."

        if sender.hours < hours:
            return "You don't have enough hours!"

        sender.hours -= hours
        receiver.hours += hours

        transaction = Transaction(sender_id=sender.id, receiver_id=receiver.id, hours=hours)
        db.session.add(transaction)
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('exchange.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
