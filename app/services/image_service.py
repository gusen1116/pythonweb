import os
import imagehash
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
from app import db, cache
from app.models.file import UploadedFile

def allowed_file(filename):
    """파일 확장자 체크"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_image_hash(img):
    """
    여러 해싱 알고리즘을 조합하여 이미지의 정교한 지문을 생성합니다.
    다양한 이미지 변형(크기 조정, 회전, 압축 등)에도 견고하게 작동합니다.
    """
    # 이미지 전처리: 크기 표준화 및 그레이스케일 변환
    img = img.convert('RGB')  # 투명도 채널 제거
    
    # 다양한 해싱 알고리즘 적용
    p_hash = imagehash.phash(img)  # 퍼셉츄얼 해시 (DCT 기반)
    d_hash = imagehash.dhash(img)  # 차분 해시 (인접 픽셀 비교)
    w_hash = imagehash.whash(img)  # 웨이블릿 해시 (웨이블릿 변환 기반)
    
    # 단일 문자열로 조합 (알고리즘의 장점 결합)
    combined_hash = f"{p_hash}_{d_hash}_{w_hash}"
    
    return combined_hash

def hash_similarity(hash1, hash2):
    """
    두 복합 해시 문자열 간의 유사도를 계산합니다.
    낮은 값일수록 이미지가 유사함을 의미합니다.
    """
    # 복합 해시 분리
    parts1 = hash1.split('_')
    parts2 = hash2.split('_')
    
    if len(parts1) != 3 or len(parts2) != 3:
        return float('inf')  # 유효하지 않은 해시 형식
    
    # 각 해시 알고리즘별 거리 계산
    p_dist = imagehash.hex_to_hash(parts1[0]) - imagehash.hex_to_hash(parts2[0])
    d_dist = imagehash.hex_to_hash(parts1[1]) - imagehash.hex_to_hash(parts2[1])
    w_dist = imagehash.hex_to_hash(parts1[2]) - imagehash.hex_to_hash(parts2[2])
    
    # 가중 평균 거리 계산 (각 알고리즘에 가중치 부여 가능)
    # 여기서는 phash에 더 높은 가중치 부여
    weighted_dist = (p_dist * 0.5) + (d_dist * 0.3) + (w_dist * 0.2)
    
    return weighted_dist

def find_similar_image(image_hash):
    """해시값을 기준으로 유사한 이미지 찾기"""
    similar_images = UploadedFile.query.filter_by(file_type='image').all()
    
    most_similar = None
    min_distance = float('inf')
    
    for existing_image in similar_images:
        if existing_image.perceptual_hash:
            distance = hash_similarity(image_hash, existing_image.perceptual_hash)
            if distance < min_distance:
                min_distance = distance
                most_similar = existing_image
    
    # 임계값 이하의 유사도를 가진 이미지가 있으면 반환
    if most_similar and min_distance <= current_app.config['IMAGE_HASH_THRESHOLD']:
        return most_similar, min_distance
    
    return None, None

def get_image_hash(img):
    """
    여러 해싱 알고리즘을 조합하여 이미지의 정교한 지문을 생성합니다.
    다양한 이미지 변형(크기 조정, 회전, 압축 등)에도 견고하게 작동합니다.
    """
    try:
        # 이미지 전처리: 크기 표준화 및 그레이스케일 변환
        img = img.convert('RGB')  # 투명도 채널 제거
        
        # 다양한 해싱 알고리즘 적용
        p_hash = imagehash.phash(img)  # 퍼셉츄얼 해시 (DCT 기반)
        d_hash = imagehash.dhash(img)  # 차분 해시 (인접 픽셀 비교)
        w_hash = imagehash.whash(img)  # 웨이블릿 해시 (웨이블릿 변환 기반)
        
        # 단일 문자열로 조합 (알고리즘의 장점 결합)
        combined_hash = f"{p_hash}_{d_hash}_{w_hash}"
        
        return combined_hash
    except Exception as e:
        # 오류 발생시 로깅 추가
        current_app.logger.error(f"이미지 해싱 중 오류 발생: {str(e)}")
        # 기본 해시 반환 (빈 문자열보다 식별 가능한 값)
        return "error_hash_0000"
    
@cache.memoize(timeout=3600)  # 1시간 캐싱
def get_image_dimensions(file_path):
    """이미지 크기 가져오기"""
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception as e:
        current_app.logger.error(f"이미지 크기 확인 중 오류 발생: {str(e)}")
        return (0, 0)