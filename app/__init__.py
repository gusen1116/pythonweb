import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from config import config
from datetime import datetime

# 확장 모듈 초기화
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'
mail = Mail()
cache = Cache()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 업로드 폴더 생성 (없을 경우)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o755)
    
    # 확장 모듈 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    
    # 템플릿 필터 등록
    from app.utils.helpers import edjs_to_html, parsejson_filter, extract_preview_filter
    app.jinja_env.filters['edjs_to_html'] = edjs_to_html
    app.jinja_env.filters['parsejson'] = parsejson_filter
    app.jinja_env.filters['extract_preview'] = extract_preview_filter
    
    # 블루프린트 등록
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.blog import blog_bp
    from app.routes.uploads import uploads_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(uploads_bp, url_prefix='/uploads')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 에러 핸들러 등록
    from app.routes import errors
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    # 로깅 설정
    if not app.debug and not app.testing:
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('MyBlog startup')
    
    return app

# 전역 컨텍스트에서 모델 import
from app.models.user import User
from app.models.post import Post
from app.models.file import UploadedFile
from app.models.category import Category
from app.models.tag import Tag
from app.models.comment import Comment

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))