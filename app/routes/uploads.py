import os
import time
from PIL import Image
from flask import Blueprint, request, jsonify, current_app, url_for
from flask_login import current_user, login_required
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from app import db
from app.models.file import UploadedFile
from app.services.image_service import get_image_hash, hash_similarity, allowed_file

uploads_bp = Blueprint('uploads', __name__)

@uploads_bp.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    return jsonify({
        'success': 0,
        'error': f'파일이 너무 큽니다. 최대 {current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)}MB까지 업로드 가능합니다.'
    }), 413

@uploads_bp.route('/image', methods=['POST'])
def upload_image():
    image_file = request.files.get('image')
    if not image_file or not allowed_file(image_file.filename):
        return jsonify({
            'success': 0,
            'error': '허용되지 않는 파일 형식입니다.'
        })

    try:
        # 파일 크기 확인
        image_file.seek(0, os.SEEK_END)
        file_size = image_file.tell()
        image_file.seek(0)
        
        # 원본 파일명에서 확장자 추출
        original_filename = secure_filename(image_file.filename)
        file_extension = os.path.splitext(original_filename)[1].lower()
        
        # 이미지 파일인지 확인
        is_image = file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        
        if is_image:
            # 이미지 파일인 경우 - 퍼셉츄얼 해싱 사용
            image_file.seek(0)
            img = Image.open(image_file)
            image_hash = get_image_hash(img)
            
            # 데이터베이스에서 모든 이미지 파일 가져오기
            similar_images = UploadedFile.query.filter_by(file_type='image').all()
            
            # 유사도 계산하여 가장 유사한 이미지 찾기
            most_similar = None
            min_distance = float('inf')
            
            for existing_image in similar_images:
                if existing_image.perceptual_hash:
                    distance = hash_similarity(image_hash, existing_image.perceptual_hash)
                    if distance < min_distance:
                        min_distance = distance
                        most_similar = existing_image
            
            # 임계값 이하의 유사도를 가진 이미지가 있으면 그 이미지를 반환
            if most_similar and min_distance <= current_app.config['IMAGE_HASH_THRESHOLD']:
                image_url = url_for('static', filename=f'uploads/{most_similar.saved_name}', _external=True)
                return jsonify(success=1, file={"url": image_url})
        else:
            # 이미지 파일이 아닌 경우 - 파일명과 크기로 중복 확인
            existing_file = UploadedFile.query.filter_by(
                original_name=original_filename,
                file_size=file_size
            ).first()
            
            if existing_file:
                # 동일한 파일명과 크기의 파일이 이미 존재함
                file_url = url_for('static', filename=f'uploads/{existing_file.saved_name}', _external=True)
                return jsonify(success=1, file={"url": file_url})
        
        # 업로드 폴더가 없으면 생성
        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
            os.makedirs(current_app.config['UPLOAD_FOLDER'], mode=0o755)
        
        # 새 파일명 생성 (타임스탬프 + 원본 파일명)
        timestamp = int(time.time())
        new_filename = f"{timestamp}_{original_filename}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
        
        # 파일 저장
        image_file.seek(0)
        if is_image:
            img = Image.open(image_file)
            
            # 이미지 형식 보존 (가능한 경우)
            if file_extension.lower() == '.png':
                if img.mode != 'RGBA' and img.mode != 'RGB':
                    img = img.convert('RGBA')
                img.save(save_path, format='PNG')
            elif file_extension.lower() in ['.jpg', '.jpeg']:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(save_path, format='JPEG', quality=90)
            else:
                # 기타 형식은 원본 형식 유지
                img.save(save_path)
            
            # 데이터베이스에 파일 정보 저장
            uploaded_file = UploadedFile(
                original_name=original_filename,
                saved_name=new_filename,
                file_size=file_size,
                file_type='image',
                perceptual_hash=image_hash,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(uploaded_file)
            db.session.commit()
        else:
            # 이미지가 아닌 파일 저장
            with open(save_path, 'wb') as f:
                image_file.seek(0)
                f.write(image_file.read())
            
            # 데이터베이스에 파일 정보 저장
            uploaded_file = UploadedFile(
                original_name=original_filename,
                saved_name=new_filename,
                file_size=file_size,
                file_type='file',
                user_id=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(uploaded_file)
            db.session.commit()
        
        # 파일 URL 반환
        file_url = url_for('static', filename=f'uploads/{new_filename}', _external=True)
        return jsonify(success=1, file={"url": file_url})
        
    except Exception as e:
        current_app.logger.error(f"파일 처리 중 오류 발생: {str(e)}")
        return jsonify(success=0, error=str(e))

@uploads_bp.route('/files', methods=['GET'])
@login_required
def list_files():
    if not current_user.is_authenticated:
        return jsonify({"success": 0, "error": "권한이 없습니다."}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 현재 사용자가 업로드한 파일만 보거나 관리자는 모든 파일 확인 가능
    if current_user.is_administrator():
        files = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).paginate(
            page=page, per_page=per_page
        )
    else:
        files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(
            UploadedFile.upload_date.desc()
        ).paginate(page=page, per_page=per_page)
    
    file_list = [{
        'id': file.id,
        'name': file.original_name,
        'size': file.file_size,
        'type': file.file_type,
        'date': file.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
        'url': url_for('static', filename=f'uploads/{file.saved_name}', _external=True)
    } for file in files.items]
    
    return jsonify({
        "success": 1, 
        "files": file_list,
        "pagination": {
            "page": files.page,
            "per_page": files.per_page,
            "total": files.total,
            "pages": files.pages
        }
    })

@uploads_bp.route('/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    
    # 파일 소유자 또는 관리자만 삭제 가능
    if file.user_id != current_user.id and not current_user.is_administrator():
        return jsonify({"success": 0, "error": "권한이 없습니다."}), 403
    
    try:
        # 물리적 파일 삭제
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.saved_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # DB에서 파일 정보 삭제
        db.session.delete(file)
        db.session.commit()
        
        return jsonify({"success": 1, "message": "파일이 삭제되었습니다."})
    except Exception as e:
        current_app.logger.error(f"파일 삭제 중 오류 발생: {str(e)}")
        return jsonify({"success": 0, "error": str(e)})