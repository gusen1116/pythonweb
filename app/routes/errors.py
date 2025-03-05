from flask import render_template, Blueprint, current_app
from app import db
from app.models.post import Post

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(400)
def bad_request_error(error):
    return render_template('errors/400.html', error=error), 400

@errors_bp.app_errorhandler(401)
def unauthorized_error(error):
    return render_template('errors/401.html', error=error), 401

@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    # 최신 게시글 가져오기
    posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    return render_template('errors/404.html', posts=posts), 404

@errors_bp.app_errorhandler(413)
def too_large_error(error):
    return render_template('errors/413.html', max_size=current_app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)), 413

@errors_bp.app_errorhandler(429)
def too_many_requests_error(error):
    return render_template('errors/429.html', error=error), 429

@errors_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()  # 오류 발생 시 DB 세션 롤백
    return render_template('errors/500.html'), 500