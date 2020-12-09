from flask import flash, render_template, url_for, redirect, g, send_from_directory, request
from project import app, db, login
from project.forms import SignUpForm, SignInForm, UserPost, FollowForm
from project.models import User, Post, Like
from project.db_seed import *
from project.db_queries import *
from flask_login import current_user, login_user, logout_user, login_required
from project import bcrypt


@app.route('/', methods= ['GET'])
def default():
    context = {}

    # Summary stats for the site
    num_likes = len(Like.query.all())
    context['num_likes'] = num_likes

    num_posts = len(Post.query.all())
    context['num_posts'] = num_posts

    num_users = len(User.query.all())
    context['num_users'] = num_users

    # a list of dicts, where each dict represents a post and related data
    # See db_queries.py >> get_all_posts_with_like_counts() for details.
    all_posts = get_all_posts_with_like_counts()
    context['posts'] = all_posts[::-1]

    return render_template('home.html', context=context)


@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        username=form.username.data
        email =form.email.data
        password = form.password.data.encode('utf-8')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('You have signed up succesfully!', 'success')
        login_user(user)
        return redirect(url_for('user_home'))
    return render_template('signUp.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        password = form.password.data.encode('utf-8')
        pw_check = bcrypt.check_password_hash(user.password, password)
        if user is None or not pw_check:
            flash('Invalid username or password')
            return redirect(url_for('signin'))
        login_user(user)
        return redirect(url_for('user_home'))
    return render_template('signIn.html', form=form)


@app.route('/signout')
@login_required
def signout():
    logout_user()
    flash('You are now signed out!', 'success')
    return redirect(url_for('signin'))


@app.route('/user/home', methods=['GET', 'POST'])
@login_required
def user_home():
    form = UserPost()
    if form.validate_on_submit():
        post = Post(content=form.content.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('user_home'))   
    posts = Post.query.order_by(Post.id.desc()).all()
    like_counts = []
    for post in posts:
        like_counts.append(get_likes_by_post_id(post.id))
    return render_template('user_home.html', posts=posts, form=form, likes=like_counts)



@app.route('/seed', methods=['POST', 'GET'])
def manage_seeding():
    return render_template('seeding.html')


@app.route('/likes', methods=['POST', 'GET'])
def show_likes():
    likes = Like.query.all()
    posts = Post.query.all()
    return render_template('likes.html', likes=likes, posts=posts)


@app.route('/likes/fill', methods=['GET'])
def create_likes():
    empty_likes()
    fill_likes()
    flash(message='Created likes.')
    return redirect(url_for('show_likes'))


@app.route('/likes/delete', methods=['GET'])
def delete_likes():
    empty_likes()
    flash('Deleted likes.', 'error')
    return redirect(url_for('show_likes'))


@app.route('/click_like', methods=['GET'])
def click_like(pst_id, usr_id):
    like = Like.query.filter(post_id=pst_id, user_id=usr_id)
    if like.count() == 0:
        temp_like = Like(user_id=usr_id, post_id=pst_id)
        db.session.add(temp_like)
    else:
        like.delete()
    db.session.commit()
    return redirect(url_for('user_home'))


@app.route('/posts/fill', methods=['GET'])
def create_posts():
    fill_posts()
    flash(message='Created posts.')
    return redirect(url_for('user_home'))


@app.route('/posts/delete', methods=['GET'])
def delete_posts():
    empty_posts()
    flash(message='Deleted posts.')
    return redirect(url_for('user_home'))


@app.route('/users/fill', methods=['GET'])
def create_users():
    fill_user()
    flash(message='Created users.')
    return redirect(url_for('user_home'))


@app.route('/users/delete', methods=['GET'])
def delete_users():
    empty_user()
    flash(message='Deleted users.')
    return redirect(url_for('user_home'))


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    form = FollowForm()
    return render_template('user.html', user=user, form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = FollowForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        current_user.follow(user)
        db.session.commit()
        flash(f'You are now following {username}!', 'success')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('user_home'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = FollowForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are no longer following {username}!', 'success')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('user_home'))


@app.route('/list_users', methods=['GET'])
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/list_posts', methods=['GET'])
def list_posts():
    posts = Post.query.all()
    return render_template('posts.html', posts=posts)


@app.route('/list_likes', methods=['GET'])
def list_likes():
    likes = Like.query.all()
    return render_template('likes.html', likes=likes)


@app.route('/reseed_all', methods=['GET'])
def reseed_all():
    fill_all_tables()
    return redirect(url_for('manage_seeding'))


@app.route('/erase_all_data', methods=['GET'])
def erase_all_data():
    empty_all_tables()
    return redirect(url_for('manage_seeding'))