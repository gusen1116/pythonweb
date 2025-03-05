import json
from datetime import datetime
from app import db
from app.models.tag import post_tags

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 외래 키
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # 관계 설정
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                          backref=db.backref('posts', lazy=True))
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    def extract_preview_data(self):
        """콘텐츠에서 미리보기용 이미지와 텍스트 추출"""
        try:
            data = json.loads(self.content)
            first_image = ""
            text_combined = ""
            
            if "blocks" in data:
                for block in data["blocks"]:
                    if block.get("type") == "image" and not first_image:
                        # 여러 이미지 구조 처리
                        if "file" in block.get("data", {}):
                            if "url" in block["data"]["file"]:
                                first_image = block["data"]["file"].get("url", "")
                        elif "url" in block.get("data", {}):
                            first_image = block["data"].get("url", "")
                    elif block.get("type") in ["paragraph", "header"]:
                        text_combined += " " + block["data"].get("text", "")
            
            return {
                "first_image": first_image,
                "text_combined": text_combined
            }
        except Exception as e:
            return {"first_image": "", "text_combined": ""}
    
    def to_dict(self):
        """포스트를 사전 형태로 변환 (API용)"""
        preview_data = self.extract_preview_data()
        
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image': preview_data['first_image'],
            'preview_text': preview_data['text_combined'][:200],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'category': self.category.name if self.category else None,
            'tags': [tag.name for tag in self.tags],
            'author': self.author.username,
            'comments_count': self.comments.count()
        }