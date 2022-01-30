from flask import Flask, render_template, redirect, url_for, flash, request, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
import stripe
import os

stripe_keys = {
  'secret_key': os.environ.get('secret_key'),
  'publishable_key': os.environ.get('publishable_key'),
}

stripe.api_key = stripe_keys['secret_key']

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(100))

    bproducts = relationship("BProducts", back_populates="author")
    sproducts = relationship("SProducts", back_populates="author")

class SProducts(db.Model):
    __tablename__ = 'sproducts'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    describe = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates='sproducts')

class BProducts(db.Model):
    __tablename__ = 'bproducts'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    describe = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates='bproducts')

db.create_all()

@app.route('/')
def home():
    prods = SProducts.query.all()
    return render_template('index.html', prods=prods, key=stripe_keys['publishable_key'], current_user=current_user)

@app.route('/add', methods=['POST', 'GET'])
def add():
    if request.method == 'POST':
        form = request.form
        new_pro = SProducts(
            url = form['url'],
            name = form['name'],
            describe = form['describe'],
            price = form['price'],
            author_id = current_user.id,
        )
        db.session.add(new_pro)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/cart', methods=['POST', 'GET'])
def cart():
    prods = current_user.bproducts
    total = 0
    for prod in prods:
        total += prod.price
    return render_template('cart.html', prods=prods, total=total*100, key=stripe_keys['publishable_key'])

@app.route('/addtocart/<int:pro_id>', methods=['GET'])
def addtocart(pro_id):
    prod = SProducts.query.get(pro_id)
    new_bp = BProducts(
        name = prod.name,
        describe = prod.describe,
        url = prod.url,
        price = prod.price,
        author_id = current_user.id,
    )
    db.session.add(new_bp)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/show/<int:pro_id>', methods=['GET', 'POST'])
def show(pro_id):
    pro = SProducts.query.get(pro_id)
    return render_template('show.html', pro=pro)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        new_user = User(
            email = form['email'],
            password = generate_password_hash(form['password'], method='pbkdf2:sha256', salt_length=8),
            username = form['username'],
        )
        is_matched = User.query.filter_by(email=form['email']).first()
        if not is_matched:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
        else:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = request.form
        user = User.query.filter_by(email=form['email']).first()
        if user:
            hashed_pass = user.password
            if check_password_hash(hashed_pass, form['password']):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('email or Password is incorrect')
                return redirect(url_for('login'))
        else:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/delete/<int:pro_id>", methods=['POST', 'GET'])
def delete(pro_id):
    pro_to_delete = BProducts.query.get(pro_id)
    db.session.delete(pro_to_delete)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route("/deletesp/<int:pro_id>", methods=['POST', 'GET'])
def deleteSp(pro_id):
    users = User.query.all()
    for user in users:
        pros_in_cart = user.bproducts
        for pro in pros_in_cart:
            if pro.id == pro_id:
                db.session.delete(pro)
                db.session.commit()
    pro_to_delete = SProducts.query.get(pro_id)
    db.session.delete(pro_to_delete)
    db.session.commit()
    return redirect(url_for('your_pros'))

@app.route('/your_pros')
def your_pros():
    prods = current_user.sproducts
    return render_template('your_pros.html', prods=prods)

@app.route('/edit/<int:pro_id>', methods=['POST', 'GET'])
def edit(pro_id):
    pro = SProducts.query.get(pro_id)
    if request.method == 'POST':
        form = request.form
        pro.url = form['url'],
        pro.name = form['name'],
        pro.describe = form['describe'],
        pro.price = form['price'],
        db.session.commit()
        return redirect(url_for('your_pros'))
    return render_template('edit.html', pro=pro)

@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    prods = current_user.bproducts
    total = 0
    for prod in prods:
        total += prod.price
        db.session.delete(prod)
        db.session.commit()

    customer = stripe.Customer.create(
        email='2landadvanture@gmail.com',
        source=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=total*100,
        currency='usd',
        description='Flask Charge'
    )



    return render_template('thanks.html', total=total)

if __name__ == '__main__':
    app.run(debug=True)
