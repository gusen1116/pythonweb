from flask import Blueprint, jsonify, request, current_app
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from app.services.search_service import search_posts
from app.utils.helpers import process_tags

api_bp = Blueprint('api', __name__)

@api_bp.route('/posts')
def get_posts():
    """무한 스크롤을 위한 게시글 API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    
    # 카테고리 또는 태그 필터
    category_slug = request.args.get('category')
    tag_slug = request.args.get('tag')
    
    # 쿼리 빌드
    query = Post.query
    
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    if tag_slug:
        tag = Tag.query.filter_by(slug=tag_slug).first()
        if tag:
            query = query.join(Post.tags).filter(Tag.id == tag.id)
    
    # 정렬 및 페이지네이션
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 결과 변환
    posts_data = [post.to_dict() for post in posts.items]
    
    return jsonify({
        'posts': posts_data,
        'has_next': posts.has_next,
        'total': posts.total,
        'pages': posts.pages,
        'page': posts.page
    })

@api_bp.route('/search')
def search_api():
    """검색 API"""
    query = request.args.get('query', '')
    if not query:
        return jsonify({'posts': [], 'total': 0})
    
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
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    search_results = search_posts(
        query=query,
        filters=filters,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    
    # 결과 변환
    posts_data = [post.to_dict() for post in search_results.items]
    
    return jsonify({
        'posts': posts_data,
        'has_next': search_results.has_next,
        'total': search_results.total,
        'page': search_results.page,
        'pages': search_results.pages,
        'query': query
    })

@api_bp.route('/categories')
def get_categories():
    """카테고리 목록 API"""
    categories = Category.query.all()
    return jsonify({
        'categories': [
            {'id': c.id, 'name': c.name, 'slug': c.slug, 'post_count': c.posts.count()}
            for c in categories
        ]
    })

@api_bp.route('/tags')
def get_tags():
    """태그 목록 API"""
    tags = Tag.query.all()
    return jsonify({
        'tags': [
            {'id': t.id, 'name': t.name, 'slug': t.slug, 'post_count': t.posts.count()}
            for t in tags
        ]
    })

@api_bp.route('/tags/suggest')
def suggest_tags():
    """태그 자동완성을 위한 API"""
    prefix = request.args.get('q', '')
    if not prefix or len(prefix) < 2:
        return jsonify({'suggestions': []})
    
    # 정확한 접두사 매치
    tags = Tag.query.filter(Tag.name.like(f'{prefix}%')).limit(10).all()
    
    if not tags:
        # 비슷한 태그 제안 추가
        similar_tags = Tag.query.filter(Tag.name.like(f'%{prefix}%')).limit(5).all()
        return jsonify({
            'suggestions': [{'id': t.id, 'name': t.name} for t in similar_tags],
            'exact_match': False
        })
    
    return jsonify({
        'suggestions': [{'id': t.id, 'name': t.name} for t in tags],
        'exact_match': True
    })