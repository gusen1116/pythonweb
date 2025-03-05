from flask import current_app
from sqlalchemy import func, or_, and_, desc
from app import db, cache
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag

@cache.memoize(timeout=300)  # 5분 캐싱
def search_posts(query, filters=None, sort_by='relevance', page=1, per_page=10):
    """
    고급 검색 기능
    
    Args:
        query: 검색어
        filters: 카테고리, 태그 등 필터 조건
        sort_by: 정렬 기준 (relevance, date, title)
        page: 페이지 번호
        per_page: 페이지당 결과 수
    
    Returns:
        검색 결과 및 페이지네이션 정보
    """
    base_query = Post.query
    
    # 필터 적용
    if filters:
        if 'category_id' in filters:
            base_query = base_query.filter(Post.category_id == filters['category_id'])
        if 'tag_id' in filters:
            base_query = base_query.join(Post.tags).filter(Tag.id == filters['tag_id'])
    
    # 검색어 적용
    if query:
        search_terms = query.split()
        search_conditions = []
        
        for term in search_terms:
            term_cond = or_(
                Post.title.ilike(f'%{term}%'),
                Post.content.ilike(f'%{term}%')
            )
            search_conditions.append(term_cond)
        
        if search_conditions:
            base_query = base_query.filter(and_(*search_conditions))
    
    # 정렬 적용
    if sort_by == 'date':
        base_query = base_query.order_by(Post.created_at.desc())
    elif sort_by == 'title':
        base_query = base_query.order_by(Post.title)
    else:  # relevance
        # SQLite에서는 전문 검색 기능이 제한적이므로 간단한 관련성 정렬 구현
        # 제목에 검색어가 포함된 경우 더 높은 점수 부여
        if query:
            # 제목과 내용에 검색어 포함 여부에 따라 정렬
            # 여기서는 간단한 정렬만 구현 (실제로는 더 복잡한 관련성 알고리즘 필요)
            base_query = base_query.order_by(
                # 제목에 검색어가 있으면 우선 정렬
                func.case(
                    [(Post.title.ilike(f'%{query}%'), 1)],
                    else_=0
                ).desc(),
                # 그 다음 최신순으로 정렬
                Post.created_at.desc()
            )
        else:
            # 검색어가 없으면 최신순 정렬
            base_query = base_query.order_by(Post.created_at.desc())
    
    # 페이지네이션 적용
    return base_query.paginate(page=page, per_page=per_page, error_out=False)

def get_search_suggestions(term, limit=10):
    """검색어 자동완성 제안"""
    # 제목에서 검색
    title_suggestions = Post.query.filter(
        Post.title.ilike(f'%{term}%')
    ).with_entities(Post.title).distinct().limit(limit).all()
    
    # 태그에서 검색
    tag_suggestions = Tag.query.filter(
        Tag.name.ilike(f'%{term}%')
    ).with_entities(Tag.name).limit(limit).all()
    
    # 카테고리에서 검색
    category_suggestions = Category.query.filter(
        Category.name.ilike(f'%{term}%')
    ).with_entities(Category.name).limit(limit).all()
    
    # 결과 통합 및 중복 제거
    suggestions = []
    
    for title in title_suggestions:
        suggestions.append({'type': 'title', 'text': title[0]})
    
    for tag in tag_suggestions:
        suggestions.append({'type': 'tag', 'text': f'#{tag[0]}'})
    
    for category in category_suggestions:
        suggestions.append({'type': 'category', 'text': f'카테고리:{category[0]}'})
    
    # 결과 제한
    return suggestions[:limit]