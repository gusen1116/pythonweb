from app import db
from app.models.comment import Comment
from app.services.email_service import send_comment_notification

def add_comment(post, content, user=None, guest_name=None, guest_email=None):
    """
    새 댓글 추가
    
    Args:
        post: 게시물 객체
        content: 댓글 내용
        user: 사용자 객체 (로그인한 경우)
        guest_name: 방문자 이름 (비로그인 시)
        guest_email: 방문자 이메일 (비로그인 시)
    
    Returns:
        생성된 댓글 객체
    """
    comment = Comment(
        content=content,
        post_id=post.id
    )
    
    if user:
        comment.user_id = user.id
        comment.is_approved = True  # 로그인 사용자 댓글은 자동 승인
    else:
        comment.guest_name = guest_name
        comment.guest_email = guest_email
        comment.is_approved = False  # 비로그인 댓글은 관리자 승인 필요
    
    db.session.add(comment)
    db.session.commit()
    
    # 댓글 알림 이메일 전송 (승인된 댓글인 경우)
    if comment.is_approved:
        send_comment_notification(post, comment)
    
    return comment

def delete_comment(comment):
    """
    댓글 삭제
    
    Args:
        comment: 삭제할 댓글 객체
    """
    db.session.delete(comment)
    db.session.commit()

def approve_comment(comment):
    """
    댓글 승인
    
    Args:
        comment: 승인할 댓글 객체
    
    Returns:
        승인된 댓글 객체
    """
    comment.is_approved = True
    db.session.commit()
    
    # 승인 후 알림 이메일 전송
    send_comment_notification(comment.post, comment)
    
    return comment

def get_pending_comments():
    """
    승인 대기 중인 댓글 목록 조회
    
    Returns:
        승인 대기 중인 댓글 목록
    """
    return Comment.query.filter_by(is_approved=False).order_by(Comment.created_at.desc()).all()

def get_comments_for_post(post_id, approved_only=True, page=1, per_page=10):
    """
    게시물의 댓글 목록 조회
    
    Args:
        post_id: 게시물 ID
        approved_only: 승인된 댓글만 조회 여부
        page: 페이지 번호
        per_page: 페이지당 댓글 수
    
    Returns:
        댓글 목록 페이지네이션 객체
    """
    query = Comment.query.filter_by(post_id=post_id)
    
    if approved_only:
        query = query.filter_by(is_approved=True)
    
    return query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=per_page)