from datetime import datetime
from app import db

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    saved_name = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    perceptual_hash = db.Column(db.String(255), nullable=True)  # 이미지인 경우 해시값 저장
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 업로드한 사용자 (옵션)
    
    def __repr__(self):
        return f'<UploadedFile {self.original_name}>'