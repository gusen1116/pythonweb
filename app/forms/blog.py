from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Optional

class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(min=1, max=200)])
    content = HiddenField('내용', validators=[DataRequired()])
    category = SelectField('카테고리', coerce=int, validators=[Optional()])
    tags = StringField('태그 (쉼표로 구분)', validators=[Optional(), Length(max=200)])
    submit = SubmitField('저장')
    
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(0, '카테고리 없음')]  # 기본 선택 항목

class CommentForm(FlaskForm):
    content = TextAreaField('댓글', validators=[DataRequired(), Length(min=1, max=1000)])
    name = StringField('이름', validators=[Length(max=100)])
    email = StringField('이메일', validators=[Length(max=100), Email()])
    submit = SubmitField('댓글 작성')

class CategoryForm(FlaskForm):
    name = StringField('카테고리명', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('설명', validators=[Optional(), Length(max=500)])
    submit = SubmitField('저장')

class SearchForm(FlaskForm):
    query = StringField('검색어', validators=[DataRequired()])
    category = SelectField('카테고리', coerce=int, validators=[Optional()])
    sort = SelectField('정렬 기준', choices=[
        ('relevance', '관련성'),
        ('date', '최신순'),
        ('title', '제목순')
    ], default='relevance')
    submit = SubmitField('검색')
    
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.category.choices = [(0, '모든 카테고리')]  # 기본 선택 항목