import json
import re
from slugify import slugify
from markupsafe import Markup, escape
from flask import current_app

def create_slug(text):
    """텍스트를 URL 슬러그로 변환"""
    # 한글 & 영문 지원 슬러그 생성 (slugify 라이브러리 사용)
    return slugify(text, allow_unicode=True)

def edjs_to_html(content_json):
    """EditorJS JSON을 HTML로 변환"""
    try:
        data = json.loads(content_json)
    except Exception as e:
        current_app.logger.error(f"JSON 파싱 오류: {e}")
        return f"<p>{escape(content_json)}</p>"  # 안전한 출력을 위한 이스케이핑

    html = ""
    
    # JSON 구조 확인
    if not isinstance(data, dict) or "blocks" not in data:
        # EditorJS 형식이 아닌 경우 안전하게 이스케이핑
        return f"<p>{escape(content_json)}</p>"
    
    # XSS 취약점을 막기 위한 안전한 태그 및 속성 목록
    ALLOWED_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol', 'li', 'img', 'a', 'figure', 'figcaption', 'pre', 'code']
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'width', 'height', 'class'],
        'figure': ['style'],
        'blockquote': ['class'],
        '*': ['style', 'class']  # 모든 태그에 허용되는 속성
    }
    
    # URL 스키마 검사 함수
    def is_safe_url(url):
        return url.startswith(('/', 'http://', 'https://', 'mailto:', 'tel:'))
    
    for block in data.get("blocks", []):
        block_type = block.get("type")
        tunes = block.get("tunes", {})
        alignment = "left"  # 기본 정렬
        
        # 정렬 튠 처리
        if "alignment" in tunes and "alignment" in tunes["alignment"]:
            alignment = tunes["alignment"]["alignment"]
        
        # 정렬 스타일 추가
        alignment_style = f' style="text-align: {alignment};"'
        
        if block_type == "paragraph":
            text = block["data"].get("text", "")
            # XSS 방지: text는 이미 HTML로 작성된 경우가 많으므로 Markup으로 처리
            html += f"<p{alignment_style}>{text}</p>"
        elif block_type == "header":
            level = block["data"].get("level", 1)
            level = max(1, min(6, level))  # 1~6 범위로 제한
            text = block["data"].get("text", "")
            html += f"<h{level}{alignment_style}>{text}</h{level}>"
        elif block_type == "image":
            url = ""
            if "file" in block["data"] and "url" in block["data"]["file"]:
                url = block["data"]["file"].get("url", "")
            elif "url" in block["data"]:
                url = block["data"].get("url", "")
                
            # URL 보안 검사
            if not is_safe_url(url):
                url = ""  # 안전하지 않은 URL 제거
                
            caption = block["data"].get("caption", "")
            
            # 이미지 크기 클래스 추가
            size = block["data"].get("size", "medium")
            size_class = f" class=\"image-size-{size}\""
            
            figure_style = f' style="text-align: {alignment};"'
            html += f'<figure{figure_style}><img src="{url}" alt="{escape(caption)}"{size_class}>'
            if caption:
                html += f'<figcaption>{caption}</figcaption>'
            html += "</figure>"
        elif block_type == "list":
            style = block["data"].get("style", "unordered")
            items = block["data"].get("items", [])
            
            if style == "ordered":
                html += f"<ol{alignment_style}>"
                for item in items:
                    html += f"<li>{item}</li>"
                html += "</ol>"
            else:
                html += f"<ul{alignment_style}>"
                for item in items:
                    html += f"<li>{item}</li>"
                html += "</ul>"
        elif block_type == "quote":
            text = block["data"].get("text", "")
            caption = block["data"].get("caption", "")
            
            html += f'<blockquote class="cdx-quote"{alignment_style}>'
            html += f'<p class="cdx-quote__text">{text}</p>'
            if caption:
                html += f'<footer class="cdx-quote__caption">{caption}</footer>'
            html += '</blockquote>'
        elif block_type == "code":
            code = block["data"].get("code", "")
            language = block["data"].get("language", "")
            
            # 코드 블록 내용 이스케이핑 (XSS 방지)
            code = escape(code)
            
            html += f'<pre{alignment_style}><code class="language-{language}">{code}</code></pre>'
        elif block_type == "embed":
            service = block["data"].get("service", "")
            source = block["data"].get("source", "")
            embed = block["data"].get("embed", "")
            caption = block["data"].get("caption", "")
            
            # 임베드 URL 보안 검사
            if source and not is_safe_url(source):
                source = ""  # 안전하지 않은 URL 제거
            
            html += f'<div class="embed-container"{alignment_style}>'
            if embed:
                html += f'{embed}'
            else:
                html += f'<iframe src="{source}" frameborder="0" allowfullscreen></iframe>'
            html += '</div>'
            
            if caption:
                html += f'<div class="embed-caption"{alignment_style}>{caption}</div>'
        elif block_type == "notice":
            message = block["data"].get("message", "")
            type_name = block["data"].get("type", "info")
            
            html += f'<div class="notice notice-{type_name}"{alignment_style}>'
            html += f'<div class="notice-title">{type_name.upper()}</div>'
            html += f'<div class="notice-message">{message}</div>'
            html += '</div>'
        else:
            text = block["data"].get("text", "")
            if not text and "content" in block.get("data", {}):
                text = block["data"].get("content", "")
            html += f"<p{alignment_style}>{text}</p>"
    
    if not html:  # 블록이 없는 경우
        html = f"<p>{escape(content_json)}</p>"
    
    return Markup(html)

def parsejson_filter(value):
    """JSON 문자열을 파이썬 객체로 변환하는 Jinja2 필터"""
    try:
        return json.loads(value)
    except Exception:
        return {}

def extract_preview_filter(content_json):
    """콘텐츠에서 미리보기용 이미지와 텍스트 추출하는 Jinja2 필터"""
    try:
        data = json.loads(content_json)
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
        current_app.logger.error(f"미리보기 데이터 추출 중 오류 발생: {e}")
        return {"first_image": "", "text_combined": ""}

def process_tags(tags_string):
    """태그 문자열을 처리하여 리스트로 변환"""
    if not tags_string:
        return []
    
    # 쉼표로 구분된 태그들을 분리하고 공백 제거
    tags = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
    
    # 중복 제거 및 빈 태그 제거
    return list(set(tags))