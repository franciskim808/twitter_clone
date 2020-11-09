from flask import Flask, render_template, url_for, redirect, flash, g, send_from_directory, request
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from forms import SignUpForm, SignInForm, UserPost
from models import User, Post, db
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_bcrypt import Bcrypt
from flask_bootstrap import Bootstrap


    # ******************************
    # Flask app object configuration
    # ******************************


app = Flask(__name__)

# Set up for password hashing
bcrypt = Bcrypt(app)

# Database configuration
# If the environment variable 'DATABASE_URL' is defined, then use it.
# Otherwise, default to the sqlite database.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        "DATABASE_URL", f"sqlite:///app.db")

# Establish a secret key
app.config['SECRET_KEY'] = 'blahblahblah'

# # Suppress the SQLALCHEMY_TRACK_MODIFICATIONS warnings in server loggin
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# set up LoginManager and initialize - used for def signIn()
login_manager = LoginManager()
login_manager.init_app(app)
bootstrap = Bootstrap(app)

# create Migrate object. See https://flask-migrate.readthedocs.io/en/latest/
migrate = Migrate(app, db)


# Set up a class for the login form
# note to self: move this to forms.py
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=3, max=12)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=1, max=20)])
    remember = BooleanField('remember me')

    
    # **********************************
    #             ROUTES
    # **********************************

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        username=form.username.data
        email =form.email.data
        hashed_pw = bcrypt.generate_password_hash(form.password.data)
      # print(username, email, hashed_pw)
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
      # flash(f'Account created for {username}!', 'success')
      # print("Account created!")
        return redirect(url_for('home')) 
    return render_template('signUp.html', form=form)


# helper function for signIn to find a user id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    #creating a dictionary to store various kinds of data to be passed to the template.
    # If the data is passed to the template, then I can 'print' it to the page.
    context = {}

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # I want a list of all users. If there are any, save to context.
        users = User.query.all()
        if users:
            context['users'] = users

        if user:
            # I'm curious what 'user' is, so I'll save it to context.
            context['user_value'] = user

            if(user.password == form.password.data):
                context['user_pwd'] = user.password
                context['form_pwd_data'] = form.password.data

                #login_user(user, remember=form.remember.data)
                # when I return, pass in the context variable.
                return render_template('home.html', context=context) + 'Hello, ' + form.username.data

        return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'
        
    
    return render_template('signIn.html', form=form)


@app.route('/signout')
@login_required
def signout():
    # Sign out using flask-login built in function
    logout_user()
    return redirect(url_for('home'))


@app.route('/user/home', methods=['GET', 'POST'])
def user_home():
    form = UserPost()
    if form.is_submitted():
        post = Post(content=form.content.data)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('user_home'))
    posts = Post.query.all()
    return render_template('user_home.html', form=form, posts=posts)




# @app.route('/db_build')
# def start_our_database_over():
#     """ An example function to show how a route can be used to rebuild and reseed the database.

#     This route can be associated with a button in the navbar to make it easy to rebuild.
#     Note: The button, and its associated route, has not been implemented in a template file.
#     """

#     # drop all tables (has not been implemented yet)

#     # re-build all tables

#     # fill in all dummy data by calling function in db_seed.py
#     db_seed.fill_all_tables()

#     # redirect to https://gritter-3308.herokuapp.com/
#     redirect(url_for('home'))
#     return



if __name__ == '__main__':
    app.run(debug=False)
