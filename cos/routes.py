import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from cos import app, db, bcrypt, mail
from cos.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                       PostForm, RequestResetForm, ResetPasswordForm, SearchForm, SearchUserForm, SearchSubjectForm)
from cos.models import User, Post, Department, Subject, Review
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password, first_name=form.first_name.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    department_list = [(i.id, i.title) for i in Department.query.all()]
    form.department_id.choices = department_list
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.department_id = form.department_id.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/search", methods=['GET', 'POST'])
def search():
    form = SearchForm()
    department_list = [(i.id, i.title) for i in Department.query.all()]
    form.department_id.choices = department_list

    if form.validate_on_submit():
        department = Department.query.filter_by(
            id=form.department_id.data).first_or_404()
        if form.submit.data:
            return redirect(url_for('user_search', department_title=department.title))
        elif form.submit2.data:
            return redirect(url_for('subject_search', department_title=department.title))
    return render_template('search.html', form=form)


@app.route("/search/user/<department_title>", methods=['GET', 'POST'])
def user_search(department_title):
    form = SearchUserForm()
    department = Department.query.filter_by(
        title=department_title).first_or_404()
    user_list = [(i.id, i.username)
                 for i in User.query.filter_by(department_id=department.id).all()]
    form.user_id.choices = user_list

    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user_id.data).first_or_404()
        return redirect(url_for('user_posts', username=user.username))
    return render_template('search_user.html', form=form)


@app.route("/search/subject/<department_title>", methods=['GET', 'POST'])
def subject_search(department_title):
    form = SearchSubjectForm()
    department = Department.query.filter_by(
        title=department_title).first_or_404()
    subject_list = [(i.id, i.title)
                    for i in Subject.query.filter_by(department_id=department.id).all()]
    form.subject_id.choices = subject_list

    if form.validate_on_submit():
        subject = Subject.query.filter_by(
            id=form.subject_id.data).first_or_404()
        return redirect(url_for('view_subject_details', subject_title=subject.title))
    return render_template('search_subject.html', form=form)


@app.route("/<department_id>/user", methods=['GET', 'POST'])
def user(department_id):
    users = User.query.filter_by(department_id=department_id).all()
    userArray = []
    for user in users:
        userObj = {}
        userObj['id'] = user.id
        userObj['username'] = user.username
        userArray.append(userObj)
    return jsonify({'users': userArray})


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/departments")
def departments():
    page = request.args.get('page', 1, type=int)
    departments = Department.query.order_by(
        Department.title.asc()).paginate(page=page, per_page=7)
    return render_template('departments.html', title='Departments', departments=departments)


@app.route("/departments/<title>")
def view_department(title):
    department = Department.query.filter_by(title=title).first_or_404()
    page = request.args.get('page', 1, type=int)
    subjects = Subject.query.filter_by(author=department).order_by(
        Subject.title.desc()).paginate(page=page, per_page=4)
    return render_template('view_department.html', department=department, subjects=subjects)


@app.route("/subjects/<subject_title>/details")
def view_subject_details(subject_title):
    subject = Subject.query.filter_by(title=subject_title).first_or_404()
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(receiver=subject)\
        .order_by(Review.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('subject_details.html', reviews=reviews, subject=subject)


@app.route("/subjects/<subject_title>/review/new", methods=['GET', 'POST'])
@login_required
def new_review(subject_title):
    subject = Subject.query.filter_by(title=subject_title).first_or_404()
    form = PostForm()
    if form.validate_on_submit():
        review = Review(title=form.title.data,
                        content=form.content.data, reviewer=current_user, receiver=subject)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been posted!', 'success')
        return redirect(url_for('home'))
    return render_template('create_review.html', title='New Review',
                           form=form, legend='New Review')
