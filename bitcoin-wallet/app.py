from flask import Flask,render_template,flash,request,redirect, send_file,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required,logout_user,current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.utils import secure_filename
import os
from bit import PrivateKey

wallet = PrivateKey('')

print(wallet.address)
print(wallet.balance)
print(wallet.to_wif())


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///mydb.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY']='SUPERSECRETKEY'
app.config['TRANSACTION_PERCENTAGE'] = 5
app.config['COMPANY_ADRESS'] = 123456789

login_manager = LoginManager(app)



class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username= db.Column(db.String(50),unique=True)
    password=db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(1000),unique=True,nullable=False)
    wallet= db.Column(db.String(1000),nullable=False)
    address = db.Column(db.String(100),nullable=False)
    amount= db.Column(db.Integer, default=0)

admin=Admin(app,name='ADMIN',template_mode='bootstrap3')
admin.add_view(ModelView(User,db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def getbalance(wallet):
    key = PrivateKey(wallet)
    newbalance = key.balance_as('usd')
    user = User.query.filter_by(wallet=wallet)
    user.amount = newbalance 
    db.session.commit()


@app.route('/')
def index():
    if current_user.is_authenticated:
        getbalance(current_user.wallet)
    return render_template('index.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST'and request.form.get('email') and request.form.get('username') and request.form.get('password'):
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if User.query.filter_by(username=username).first():
            flash('Username taken')
            return render_template('signup.html')
       
        else:
            wallet = PrivateKey()
            user = User(username=username, password=password, email=email, address=wallet.address, wallet=wallet.to_wif())
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))

    elif request.method == 'POST':
        flash('Check your input')
    else:
        return render_template('signup.html')

    return render_template('signup.html')


@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            user = User.query.filter_by(username=username).first()
            if user.password == password:
                login_user(user)
                flash('YOU ARE NOW LOGGED IN')
                return redirect(url_for('index'))
            else: 
                flash('wrong Password')
                return render_template('login.html')
        else:
            flash('USER DOES NOT EXIST')
            return render_template('login.html')

    return render_template('login.html')

def createuser(username,password):
    user = User(username=username,password=password)
    db.session.add(user)
    db.session.commit() 

@app.route('/transaction', methods=['POST', 'GET'])
def transaction():
    getbalance(current_user.wallet)

    if request.method == 'POST' and request.form.get('amount') and request.form.get('address'):
        if current_user.wallet < int(amount):
            flash('not enough funds')
            return render_template('transaction.html')
            
        amount = request.form.get('amount')
        address = request.form.get('address')
        key = PrivateKey(current_user.wallet)
        myamount = (app.config['TRANSACTION_PERCENTAGE'])/100 * amount
        youramount = amount -myamount
        transactionid = key.send([(address,youramount, 'usd'), (app.config['COMPANY_ADRESS'], myamount, 'usd')])
        flash('transaction succeded transactionid ={transactionid}')
    return render_template('transaction.html')



if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
