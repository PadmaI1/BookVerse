from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, PasswordField, TextAreaField 
from wtforms.validators import DataRequired, URL, EqualTo, Length
from flask_wtf.file import FileField, FileAllowed

'''
all inherit:

CSRF protection
Validation framework
validate_on_submit()
hidden_tag()
Error handling
Form processing

from FlaskForm.
'''
class BookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    genre = StringField("Genre", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    image = StringField("Image URL", validators=[DataRequired(), URL()])
    rating = FloatField("Rating", validators=[DataRequired()])
    submit = SubmitField("Submit")

class RegistrationForm(FlaskForm):

    username = StringField("Username", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ChatForm(FlaskForm):

    content = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")

class EditProfileForm(FlaskForm):

    username = StringField("Username", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    profile_pic = FileField("Profile Picture", validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")])

    submit = SubmitField("Update")

class ChangePasswordForm(FlaskForm):

    current_password = StringField("Current Password", validators=[DataRequired()])
    new_password = StringField("New Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = StringField("Confirm Password", validators=[DataRequired(), EqualTo("new_password", message="Passwords must match")])
    submit = SubmitField("Change Password")

