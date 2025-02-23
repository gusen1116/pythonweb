import os
import uuid
import markdown
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# 최대 업로드 크기를 100MB로 설정 (4K 이미지 지원)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# SQLite 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# UPLOAD_FOLDER 설정
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 허용할 파일 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# 데이터베이스 초기화
db = SQLAlchemy(app)
migrate = Migrate(app, db)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 파일 크기 초과 오류 핸들러
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    return "파일이 너무 큽니다. 최대 100MB까지 업로드 가능합니다.", 413

# DB 모델 정의
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300), nullable=True)
    use_markdown = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Post {self.title}>"

# 라우트
@app.route("/")
def home():
    posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    return render_template("index.html", posts=posts)

@app.route("/blog")
def blog():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("blog.html", posts=posts)

@app.route("/blog/new", methods=['GET', 'POST'])
def blog_new():
    if request.method == 'POST':
        title = request.form.get("title")
        # content는 Editor.js 에서 저장한 JSON을 받음; 필요에 따라 서버측에서 처리
        content = request.form.get("content")
        use_markdown = request.form.get("is_markdown", "false").lower() == "true"
        if use_markdown:
            content = markdown.markdown(content)
        tags = request.form.get("tags")
        category = request.form.get("category")
        uploaded_image_url = request.form.get("uploaded_image")  # AJAX 이미지 업로드 URL
        
        post = Post(
            title=title,
            content=content,
            image=uploaded_image_url,
            use_markdown=use_markdown,
            tags=tags,
            category=category
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("blog"))
    return render_template("blog_new.html")

@app.route("/blog/<int:post_id>")
def blog_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("blog_detail.html", post=post, post_id=post.id)

@app.route("/blog/<int:post_id>/edit", methods=['GET', 'POST'])
def blog_edit(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form.get("title")
        post.content = request.form.get("content")
        post.use_markdown = request.form.get("is_markdown", "false").lower() == "true"
        if post.use_markdown:
            post.content = markdown.markdown(post.content)
        post.tags = request.form.get("tags")
        post.category = request.form.get("category")
        db.session.commit()
        return redirect(url_for("blog_detail", post_id=post.id))
    return render_template("blog_edit.html", post=post, post_id=post.id)

@app.route("/blog/<int:post_id>/delete", methods=['POST'])
def blog_delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("blog"))

@app.route('/project')
def project():
    return render_template('project.html')

@app.route("/simulation")
def simulation():
    return render_template("simulation.html")

# 이미지 업로드 전용 엔드포인트 (POST 요청)
@app.route('/upload_image', methods=['POST'])
def upload_image():
    image_file = request.files.get('image')
    if image_file and allowed_file(image_file.filename):
        try:
            image_file.seek(0)
            img = Image.open(image_file)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            filename = f"{uuid.uuid4().hex}.png"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            img.save(save_path, format='PNG')
            image_url = url_for('static', filename=f'uploads/{filename}')
            return jsonify(success=True, url=image_url)
        except Exception as e:
            print("이미지 처리 중 오류 발생:", e)
            return jsonify(success=False, error=str(e))
    else:
        return jsonify(success=False, error="허용되지 않는 파일 형식입니다.")

# 마크다운 미리보기 전용 엔드포인트 (POST 요청)
@app.route('/preview_content', methods=['POST'])
def preview_content():
    content = request.form.get("content", "")
    # HTML 태그로 시작하지 않으면 마크다운 변환 수행
    if not content.strip().startswith("<"):
        rendered = markdown.markdown(content, extensions=['extra', 'fenced_code', 'codehilite'])
    else:
        rendered = content
    return jsonify(success=True, html=rendered)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("Upload folder:", app.config['UPLOAD_FOLDER'])
    app.run(debug=True, host='0.0.0.0', port=8080)