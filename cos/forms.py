from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import RadioField, IntegerField, SelectField, StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired, Required
from cos.models import User, Department


class SortForm(FlaskForm):
    sort = SelectField('Sort by', coerce=int, choices=[(1, 'Rating (High to Low)'), (
        2, 'Rating (Low to High)'), (3, 'Title (alphabetical order)'), (4, 'Subject Code')])
    submit = SubmitField('Go')


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    first_name = StringField('First Name',
                             validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name',
                            validators=[Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])

    department_id = SelectField(
        'Department', coerce=int)

    title = SelectField(
        'Title', coerce=int, validators=[InputRequired()])

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
    picture = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    'That username is taken. Please choose a different one.')


class SearchForm(FlaskForm):
    department_id = SelectField(
        'Department', coerce=int, validators=[InputRequired()])
    submit = SubmitField('Search Users')
    submit2 = SubmitField('Search Subjects')


class ModifyForm(FlaskForm):
    submit = SubmitField('Modify Subject')
    submit2 = SubmitField('Modify Department')


class ModifySubjectForm(FlaskForm):
    title = StringField('Title')
    code = StringField('Code')
    slot = StringField('Slot')
    content = TextAreaField('Content')
    department_id = IntegerField('Department ID')
    submit = SubmitField('Add subject')

    title_delete = StringField('Title')
    submit2 = SubmitField('Delete Subject')


class ModifyDepartmentForm(FlaskForm):
    title = StringField('Title')
    submit = SubmitField('Add subject')

    title_delete = StringField('Title')
    submit2 = SubmitField('Delete Subject')


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


class ReviewForm(FlaskForm):
    rating = SubmitField(
        'Rating', validators=[InputRequired()])
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
