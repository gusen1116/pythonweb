from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import current_user, login_required
from app import db
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from app.models.comment import Comment
from app.forms.blog import PostForm, CommentForm, CategoryForm, SearchForm
from app.services.post_service import create_post, update_post, delete_post, get_related_posts
from app.services.search_service import search_posts
from app.utils.helpers import process_tags

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
    )
    return render_template('main/blog.html', 
                           title='블로그', 
                           posts=posts.items,
                           page=page,
                           total_pages=posts.pages)

@blog_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    
    comments = Comment.query.filter_by(post_id=post_id, is_approved=True).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=current_app.config['COMMENTS_PER_PAGE'])
    
    # 댓글 폼
    form = CommentForm()
    
    # 이전/다음 글
    prev_post = Post.query.filter(Post.id < post_id).order_by(Post.id.desc()).first()
    next_post = Post.query.filter(Post.id > post_id).order_by(Post.id.asc()).first()
    
    # 관련 글
    related_posts = get_related_posts(post)
    
    return render_template('blog/post_detail.html', 
                           title=post.title,
                           post=post,
                           comments=comments.items,
                           pagination=comments,
                           form=form,
                           prev_post=prev_post,
                           next_post=next_post,
                           related_posts=related_posts)

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            post_id=post_id
        )
        
        if current_user.is_authenticated:
            comment.user_id = current_user.id
            comment.is_approved = True
        else:
            comment.guest_name = form.name.data
            comment.guest_email = form.email.data
            comment.is_approved = False  # 관리자 승인 필요
            
        db.session.add(comment)
        db.session.commit()
        
        if comment.is_approved:
            flash('댓글이 등록되었습니다.')
        else:
            flash('댓글이 등록되었습니다. 관리자 승인 후 게시됩니다.')
        
        return redirect(url_for('blog.post_detail', post_id=post_id))
    
    # 폼 검증 실패
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'"{getattr(form, field).label.text}" 필드에서 오류: {error}', 'error')
    
    return redirect(url_for('blog.post_detail', post_id=post_id))

@blog_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    
    # 삭제 권한 확인 (댓글 작성자, 게시물 작성자, 관리자)
    if not (current_user.id == comment.user_id or 
            current_user.id == comment.post.user_id or 
            current_user.is_administrator()):
        abort(403)
    
    db.session.delete(comment)
    db.session.commit()
    flash('댓글이 삭제되었습니다.')
    
    return redirect(url_for('blog.post_detail', post_id=post_id))

# 수정된 new_post 라우트 - 로그인 없이 글 작성 가능
@blog_bp.route('/new', methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    form.category.choices = [(0, '카테고리 없음')] + [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if form.validate_on_submit():
        # 태그 처리
        tags = process_tags(form.tags.data)
        
        # 임시로 기본 사용자 ID 설정 (예: 관리자 계정의 ID)
        default_user_id = 1  # 첫 번째 사용자(보통 관리자)의 ID
        
        post = create_post(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category.data if form.category.data != 0 else None,
            tags=tags,
            user_id=default_user_id  # 로그인 없이도 글 작성 가능
        )
        
        flash('포스트가 성공적으로 작성되었습니다.')
        return redirect(url_for('blog.post_detail', post_id=post.id))
    
    return render_template('blog/post_editor.html', title='새 글 작성', form=form)

# 수정된 edit_post 라우트 - 로그인 및 권한 확인 제거
@blog_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 권한 확인 로직 제거 또는 완화
    
    form = PostForm()
    form.category.choices = [(0, '카테고리 없음')] + [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if form.validate_on_submit():
        # 태그 처리
        tags = process_tags(form.tags.data)
        
        update_post(
            post,
            title=form.title.data,
            content=form.content.data,
            category_id=form.category.data if form.category.data != 0 else None,
            tags=tags
        )
        
        flash('포스트가 성공적으로 수정되었습니다.')
        return redirect(url_for('blog.post_detail', post_id=post.id))
    elif request.method == 'GET':
        # 폼에 기존 데이터 채우기
        form.title.data = post.title
        form.content.data = post.content
        form.category.data = post.category_id if post.category_id else 0
        form.tags.data = ', '.join([tag.name for tag in post.tags])
    
    return render_template('blog/post_editor.html', title='글 수정', form=form, post=post)

@blog_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post_route(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 권한 확인 (작성자 또는 관리자만 삭제 가능)
    if post.user_id != current_user.id and not current_user.is_administrator():
        abort(403)
    
    delete_post(post)
    flash('포스트가 삭제되었습니다.')
    
    return redirect(url_for('blog.index'))

@blog_bp.route('/category/<slug>')
def category(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.filter_by(category_id=category.id).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    
    return render_template('blog/blog.html',
                           title=f'카테고리: {category.name}',
                           posts=posts.items,
                           page=page,
                           total_pages=posts.pages,
                           category=category)

@blog_bp.route('/tag/<slug>')
def tag(slug):
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.join(Post.tags).filter(
        Tag.id == tag.id
    ).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    
    return render_template('blog/blog.html',
                           title=f'태그: {tag.name}',
                           posts=posts.items,
                           page=page,
                           total_pages=posts.pages,
                           tag=tag)

@blog_bp.route('/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('blog.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    
    # 검색 필터
    filters = {}
    category_slug = request.args.get('category')
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            filters['category_id'] = category.id
    
    tag_slug = request.args.get('tag')
    if tag_slug:
        tag = Tag.query.filter_by(slug=tag_slug).first()
        if tag:
            filters['tag_id'] = tag.id
    
    # 정렬 기준
    sort_by = request.args.get('sort', 'relevance')
    
    search_results = search_posts(
        query=query,
        filters=filters,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    
    return render_template('blog/search.html',
                           title=f'검색 결과: {query}',
                           query=query,
                           posts=search_results.items,
                           page=page,
                           total_pages=search_results.pages)

@blog_bp.route('/admin/comments')
@login_required
def admin_comments():
    if not current_user.is_administrator():
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(is_approved=False).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=20)
    
    return render_template('blog/admin_comments.html',
                           title='댓글 관리',
                           comments=comments.items,
                           pagination=comments)

@blog_bp.route('/admin/comment/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    if not current_user.is_administrator():
        abort(403)
    
    comment = Comment.query.get_or_404(comment_id)
    comment.is_approved = True
    db.session.commit()
    
    flash('댓글이 승인되었습니다.')
    return redirect(url_for('blog.admin_comments'))