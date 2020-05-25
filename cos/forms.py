from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import SelectField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired
from cos.models import User, Department


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    first_name = StringField('First Name',
                             validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[
                        FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')
    department_id = SelectField(
        'Department', coerce=int, validators=[InputRequired()])
    # department_id = SelectField('Department', choices=[(1, 'Aerospace Engineering'), (2, 'Agricultural and Food Engineering'), (3, 'Architecture and Regional Planning'), (4, 'Biotechnology'), (5, 'Chemical Engineering'), (6, 'Chemistry'), (7, 'Civil Engineering'), (8, 'Computer Science and Engineering'), (9, 'Electrical Engineering'), (10, 'Electronics and Elctrical Communication Engineering'), (
    #  11, 'Geology and Geophysics'), (12, 'Humanities and Social Sciences'), (13, 'Industrial and Systems Engineering'), (14, 'Mathematics'), (15, 'Mechanical Engineering'), (16, 'Metallurgical and Materials Engineering'), (17, 'Mining Engineering'), (18, 'Ocean Engineering and Naval Architecture'), (19, 'Physics')], validators=[DataRequired()])

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    'That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    'That email is taken. Please choose a different one.')


class SearchForm(FlaskForm):
    department_id = SelectField(
        'Department', coerce=int, validators=[InputRequired()])
    submit = SubmitField('Search Users')
    submit2 = SubmitField('Search Subjects')


class SearchUserForm(FlaskForm):
    user_id = SelectField(
        'User', coerce=int, validators=[InputRequired()])
    submit = SubmitField('Go')


class SearchSubjectForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int,
                             validators=[InputRequired()])
    submit = SubmitField('Go')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError(
                'There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
