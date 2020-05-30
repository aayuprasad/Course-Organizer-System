import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, Markup
from cos import app, db, bcrypt, mail
from cos.forms import (SortForm, RegistrationForm, LoginForm, UpdateAccountForm,
                       PostForm, RequestResetForm, ResetPasswordForm, SearchForm, SearchUserForm, SearchSubjectForm, ModifyForm, ModifySubjectForm, ModifyDepartmentForm, ReviewForm)
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


@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.id != 1:
        flash('Access denied!', danger)
        return redirect(url_for('home'))
    else:
        form = ModifyForm()
        if form.submit.data:
            return redirect(url_for('modify_subject'))
        elif form.submit2.data:
            return redirect(url_for('modify_department'))
    return render_template('admin.html', form=form)


@app.route("/admin/modify_subject", methods=['GET', 'POST'])
@login_required
def modify_subject():
    form = ModifySubjectForm()
    if current_user.id != 1:
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    else:
        if form.submit.data:
            subject = Subject(title=form.title.data, content=form.content.data,
                              department_id=form.department_id.data, code=form.code.data, slot=form.slot.data)
            db.session.add(subject)
            db.session.commit()
            flash('Subject added!', 'success')
        elif form.submit2.data:
            subject = Subject.query.filter_by(
                title=form.title_delete.data).first_or_404()
            db.session.delete(subject)
            db.session.commit()
            flash('Subject deleted!', 'danger')
    return render_template('modify_subject.html', form=form)


@app.route("/admin/modify_department", methods=['GET', 'POST'])
@login_required
def modify_department():
    form = ModifyDepartmentForm()
    if current_user.id != 1:
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    else:
        if form.submit.data:
            department = Department(title=form.title.data)
            db.session.add(department)
            db.session.commit()
            flash('Department added!', 'success')
        elif form.submit2.data:
            department = Department.query.filter_by(
                title=form.title_delete.data).first_or_404()
            db.session.delete(department)
            db.session.commit()
            flash('Department deleted!', 'danger')
    return render_template('modify_department.html', form=form)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    department_list = [(i.id, i.title) for i in Department.query.all()]
    title_list = [(1, 'Student'), (2, 'Teacher')]
    form = RegistrationForm()
    form.department_id.choices = department_list
    form.title.choices = title_list

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        department_id = form.department_id.data
        title = form.title.data
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password, first_name=form.first_name.data, last_name=form.last_name.data, department_id=department_id, title=title)

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
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
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


@app.route("/students")
@login_required
def students():
    page = request.args.get('page', 1, type=int)
    students = User.query.filter_by(title='1').order_by(
        User.username.asc()).paginate(page=page, per_page=5)
    department_list = [i.title for i in Department.query.all()]
    return render_template('students.html', students=students, department_list=department_list)


@app.route("/teachers")
@login_required
def teachers():
    page = request.args.get('page', 1, type=int)
    teachers = User.query.filter_by(title='2').order_by(
        User.username.asc()).paginate(page=page, per_page=5)
    department_list = [i.title for i in Department.query.all()]
    return render_template('teachers.html', teachers=teachers, department_list=department_list)


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
@login_required
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    department = Department.query.filter_by(
        id=user.department_id).first_or_404()
    department_title = department.title
    return render_template('user_posts.html', posts=posts, user=user, department_title=department_title)


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


@app.route("/departments/<title>", methods=['POST', 'GET'])
def view_department(title):
    form = SortForm()
    department = Department.query.filter_by(title=title).first_or_404()
    page = request.args.get('page', 1, type=int)
    subjects = Subject.query.paginate(page=page, per_page=4)
    if form.submit.data:
        if form.sort.data == 1:
            subjects = Subject.query.filter_by(author=department).order_by(
                Subject.average_rating.desc()).paginate(page=page, per_page=4)
        elif form.sort.data == 2:
            subjects = Subject.query.filter_by(author=department).order_by(
                Subject.average_rating.asc()).paginate(page=page, per_page=4)
        elif form.sort.data == 3:
            subjects = Subject.query.filter_by(author=department).order_by(
                Subject.title.asc()).paginate(page=page, per_page=4)
        elif form.sort.data == 4:
            subjects = Subject.query.filter_by(author=department).order_by(
                Subject.code.asc()).paginate(page=page, per_page=4)
    return render_template('view_department.html', department=department, subjects=subjects, form=form)


@app.route("/subjects/<subject_title>/details")
@login_required
def view_subject_details(subject_title):
    subject = Subject.query.filter_by(title=subject_title).first_or_404()
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(receiver=subject)\
        .order_by(Review.date_posted.desc())

    labels = ['5', '4.5', '4', '3.5', '3', '2.5', '2', '1.5', '1', '.5']
    values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    colors = ["#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
              "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1", "#C71585", "#FF4500"]

    total = 0
    x = 0
    for review in reviews:
        total = total + review.rating
        x = x + 1
        index = int(10 - 2 * review.rating)
        values[index] = values[index] + 1
    maxi = max(values)
    if x != 0:
        average_rating = float(total / x)
        subject.average_rating = average_rating
        db.session.commit()
        average_rating = "{0:.3f}".format(average_rating)
    else:
        average_rating = 0
    reviews = Review.query.filter_by(receiver=subject)\
        .order_by(Review.date_posted.desc())\
        .paginate(page=page, per_page=5)

    user_review = Review.query.filter_by(
        user_id=current_user.id, receiver=subject).first()
    if not user_review:
        legend = 'Add Review'
    else:
        legend = 'Modify Review'
    return render_template('subject_details.html', reviews=reviews, subject=subject, legend=legend, average_rating=average_rating, labels=labels, values=values, max=maxi)


@app.route("/subjects/<subject_title>/review/new", methods=['GET', 'POST'])
@login_required
def new_review(subject_title):
    subject = Subject.query.filter_by(title=subject_title).first_or_404()
    form = ReviewForm()
    legend = 'Add Review'
    user_review = Review.query.filter_by(
        subject_id=subject.id, user_id=current_user.id).first()
    if user_review:
        legend = 'Modify Review'
    if form.validate_on_submit():
        rating = request.form['rating']
        if rating == "5":
            subject_rating = 5
        elif rating == "4 and a half":
            subject_rating = 4.5
        elif rating == "4":
            subject_rating = 4
        elif rating == "3 and a half":
            subject_rating = 3.5
        elif rating == "3":
            subject_rating = 3
        elif rating == "2 and a half":
            subject_rating = 2.5
        elif rating == "2":
            subject_rating = 2
        elif rating == "1 and a half":
            subject_rating = 1.5
        elif rating == "1":
            subject_rating = 1
        elif rating == "half":
            subject_rating = 0.5
        else:
            subject_rating = 0
        if legend == 'Modify Review':
            db.session.delete(user_review)
            db.session.commit()
        review = Review(title=form.title.data,
                        content=form.content.data, reviewer=current_user, receiver=subject, rating=subject_rating)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been posted!', 'success')
        return redirect(url_for('view_subject_details', subject_title=subject_title))
    elif request.method == 'GET' and user_review:
        form.title.data = user_review.title
        form.content.data = user_review.content
    return render_template('create_review.html', title='Add Review',
                           form=form, legend=legend, review=user_review)


@app.route("/review/<int:review_id>/delete", methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    subject = Subject.query.filter_by(id=review.subject_id).first()
    if review.reviewer != current_user:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash('Your review has been deleted!', 'danger')
    return redirect(url_for('view_subject_details', subject_title=subject.title))


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user_posts', username=username))
    u = current_user.follow(user)
    if u is None:
        flash('Cannot follow ' + username + '.')
        return redirect(url_for('user_posts', username=username))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + username + '!', 'success')
    return redirect(url_for('user_posts', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user_posts', username=username))
    u = current_user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + username + '.')
        return redirect(url_for('user_posts', username=username))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + username + '.', 'danger')
    return redirect(url_for('user_posts', username=username))


@app.route("/subjects", methods=['POST', 'GET'])
def subjects():
    form = SortForm()
    page = request.args.get('page', 1, type=int)
    subjects = Subject.query.paginate(page=page, per_page=6)
    if form.submit.data:
        if form.sort.data == 1:
            subjects = Subject.query.order_by(
                Subject.average_rating.desc()).paginate(page=page, per_page=6)
        elif form.sort.data == 2:
            subjects = Subject.query.order_by(
                Subject.average_rating.asc()).paginate(page=page, per_page=6)
        elif form.sort.data == 3:
            subjects = Subject.query.order_by(
                Subject.title.asc()).paginate(page=page, per_page=6)
        elif form.sort.data == 4:
            subjects = Subject.query.order_by(
                Subject.code.asc()).paginate(page=page, per_page=6)

    return render_template('subjects.html', subjects=subjects, form=form)
