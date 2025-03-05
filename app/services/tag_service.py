from app import db
from app.models.tag import Tag
from app.utils.helpers import create_slug

def get_or_create_tag(name):
    """
    태그 이름으로 태그 객체를 조회하거나 생성
    
    Args:
        name: 태그 이름
        
    Returns:
        태그 객체
    """
    name = name.strip()
    tag = Tag.query.filter_by(name=name).first()
    
    if not tag:
        slug = create_slug(name)
        # 슬러그 중복 확인 및 처리
        existing_slug = Tag.query.filter_by(slug=slug).first()
        if existing_slug:
            i = 1
            while Tag.query.filter_by(slug=f"{slug}-{i}").first():
                i += 1
            slug = f"{slug}-{i}"
        
        tag = Tag(name=name, slug=slug)
        db.session.add(tag)
        db.session.commit()
    
    return tag

def process_tags_text(tags_text):
    """
    쉼표로 구분된 태그 문자열을 처리하여 태그 객체 목록 반환
    
    Args:
        tags_text: 쉼표로 구분된 태그 문자열
        
    Returns:
        태그 객체 목록
    """
    tag_names = [name.strip() for name in tags_text.split(',') if name.strip()]
    tag_objects = []
    
    for name in tag_names:
        tag = get_or_create_tag(name)
        tag_objects.append(tag)
    
    return tag_objects

def get_popular_tags(limit=10):
    """
    가장 많이 사용된 태그 목록 조회
    
    Args:
        limit: 조회할 태그 수
        
    Returns:
        인기 태그 목록
    """
    return Tag.query.join(Tag.posts).group_by(Tag.id).order_by(
        db.func.count().desc()
    ).limit(limit).all()

def update_tag(tag, new_name):
    """
    태그 이름 업데이트
    
    Args:
        tag: 수정할 태그 객체
        new_name: 새 태그 이름
        
    Returns:
        업데이트된 태그 객체
    """
    tag.name = new_name.strip()
    tag.slug = create_slug(tag.name)
    db.session.commit()
    return tag

def delete_tag(tag):
    """
    태그 삭제
    
    Args:
        tag: 삭제할 태그 객체
    """
    db.session.delete(tag)
    db.session.commit()