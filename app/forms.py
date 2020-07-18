#validate_ methods automatically called upon validate_on_submit()

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed #To add file upload support
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
            
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class PostForm(FlaskForm): 
    dare = FileField('Upload your dare!', 
                    validators=[FileRequired(), 
                    FileAllowed(['mp4', 'webm'], 'Videos only!')])
    post = TextAreaField('Write a caption!', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')
    
class CommentForm(FlaskForm):
    comment = TextAreaField('Enter a comment!', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')
    
class ReportForm(FlaskForm):
    reason = TextAreaField('Please state why this post is inappropriate', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')
    
class BanForm(FlaskForm):
    reason = TextAreaField('Reason for ban:', validators=[
        DataRequired(), Length(min=1, max=30)])
    submit = SubmitField('Ban')
            
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')
    
    #Used instead of current_user.username to reduce dependency on Flask-Login
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username: #If change to username
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
                
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField(
        'Repeat New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change password')
                
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
    
class SearchProfileForm(FlaskForm):
    username = StringField('Search user')
    submit = SubmitField('Search')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user is None:
            raise ValidationError('Username not Found')

class MessageForm(FlaskForm):
    message = TextAreaField('Enter a message!', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Send')
