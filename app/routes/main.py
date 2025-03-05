from flask import Blueprint, render_template, current_app
from app import cache, db  # db import 추가
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@cache.cached(timeout=300)  # 5분 캐싱
def index():
    # 최신 글 가져오기
    posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    
    # 인기 카테고리 가져오기
    popular_categories = Category.query.join(Post).group_by(Category.id).order_by(
        db.func.count(Post.id).desc()
    ).limit(5).all()
    
    # 인기 태그 가져오기
    popular_tags = Tag.query.join(Tag.posts).group_by(Tag.id).order_by(
        db.func.count().desc()
    ).limit(10).all()
    
    return render_template(
        'main/index.html',
        title='홈',
        posts=posts,
        popular_categories=popular_categories,
        popular_tags=popular_tags
    )

@main_bp.route('/about')
def about():
    return render_template('main/about.html', title='소개')

@main_bp.route('/project')
def project():
    return render_template('main/project.html', title='프로젝트')

@main_bp.route('/simulation')
def simulation():
    return render_template('main/simulation.html', title='시뮬레이션')