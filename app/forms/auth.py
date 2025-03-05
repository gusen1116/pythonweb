from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User
class LoginForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')

class RegistrationForm(FlaskForm):
    username = StringField('사용자 이름', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('비밀번호 확인', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('가입하기')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('이미 사용 중인 사용자 이름입니다.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('이미 사용 중인 이메일 주소입니다.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    submit = SubmitField('비밀번호 재설정 요청')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('새 비밀번호', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('비밀번호 확인', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('비밀번호 변경')