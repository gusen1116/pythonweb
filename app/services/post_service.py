from datetime import datetime
from slugify import slugify
from flask import current_app
from app import db
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from app.utils.helpers import process_tags

def create_post(title, content, category_id=None, tags=None, user_id=None):
    """새 포스트 생성"""
    post = Post(
        title=title,
        content=content,
        user_id=user_id
    )
    
    # 카테고리 설정
    if category_id:
        post.category_id = category_id
    
    # 태그 처리
    if tags:
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                # 새 태그 생성
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                db.session.add(tag)
            post.tags.append(tag)
    
    db.session.add(post)
    db.session.commit()
    return post

def update_post(post, title, content, category_id=None, tags=None):
    """포스트 수정"""
    post.title = title
    post.content = content
    post.updated_at = datetime.utcnow()
    
    # 카테고리 업데이트
    post.category_id = category_id
    
    # 태그 업데이트
    if tags is not None:
        # 기존 태그 제거
        post.tags = []
        
        # 새 태그 추가
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                # 새 태그 생성
                tag = Tag(name=tag_name, slug=slugify(tag_name))
                db.session.add(tag)
            post.tags.append(tag)
    
    db.session.commit()
    return post

def delete_post(post):
    """포스트 삭제"""
    db.session.delete(post)
    db.session.commit()

def get_related_posts(post, limit=3):
    """관련 포스트 가져오기"""
    related_posts = []
    
    # 1. 같은 카테고리 글
    if post.category_id:
        category_posts = Post.query.filter(
            Post.category_id == post.category_id,
            Post.id != post.id
        ).order_by(Post.created_at.desc()).limit(limit).all()
        
        related_posts.extend(category_posts)
    
    # 2. 같은 태그를 가진 글
    if len(related_posts) < limit and post.tags:
        tag_ids = [tag.id for tag in post.tags]
        tag_posts = Post.query.join(Post.tags).filter(
            Tag.id.in_(tag_ids),
            Post.id != post.id,
            ~Post.id.in_([p.id for p in related_posts])  # 중복 방지
        ).order_by(Post.created_at.desc()).limit(limit - len(related_posts)).all()
        
        related_posts.extend(tag_posts)
    
    # 3. 최신 글로 채우기
    if len(related_posts) < limit:
        recent_posts = Post.query.filter(
            Post.id != post.id,
            ~Post.id.in_([p.id for p in related_posts])  # 중복 방지
        ).order_by(Post.created_at.desc()).limit(limit - len(related_posts)).all()
        
        related_posts.extend(recent_posts)
    
    return related_posts

def get_post_statistics():
    """포스트 통계 정보 가져오기"""
    total_posts = Post.query.count()
    categories_count = db.session.query(
        Category.name, db.func.count(Post.id)
    ).join(Post).group_by(Category.id).all()
    
    tags_count = db.session.query(
        Tag.name, db.func.count(Post.id)
    ).join(Tag.posts).group_by(Tag.id).all()
    
    monthly_posts = db.session.query(
        db.func.strftime('%Y-%m', Post.created_at).label('month'),
        db.func.count(Post.id)
    ).group_by('month').order_by('month').all()
    
    return {
        'total_posts': total_posts,
        'categories': categories_count,
        'tags': tags_count,
        'monthly_posts': monthly_posts
    }