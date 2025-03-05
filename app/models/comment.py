from datetime import datetime
from app import db

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_approved = db.Column(db.Boolean, default=False, index=True)
    
    # 외래 키
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 로그인한 사용자
    
    # 비로그인 사용자 정보
    guest_name = db.Column(db.String(100), nullable=True)
    guest_email = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<Comment {self.id}>'