from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from app import mail

def send_async_email(app, message):
    """비동기적으로 이메일 전송"""
    with app.app_context():
        mail.send(message)

def send_email(subject, sender, recipients, text_body, html_body):
    """이메일 전송 헬퍼 함수"""
    message = Message(subject, sender=sender, recipients=recipients)
    message.body = text_body
    message.html = html_body
    
    # 비동기 이메일 전송 (백그라운드 스레드)
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), message)
    ).start()

def send_password_reset_email(user):
    """비밀번호 재설정 이메일 전송"""
    token = user.get_reset_password_token()
    send_email(
        '[MyBlog] 비밀번호 재설정',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template(
            'email/reset_password.txt',
            user=user,
            token=token
        ),
        html_body=render_template(
            'email/reset_password.html',
            user=user,
            token=token
        )
    )

def send_comment_notification(post, comment):
    """새 댓글 알림 이메일 전송"""
    if not post.author or not post.author.email:
        return
    
    send_email(
        f'[MyBlog] "{post.title}" 게시글에 새 댓글이 있습니다',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[post.author.email],
        text_body=render_template(
            'email/new_comment.txt',
            post=post,
            comment=comment
        ),
        html_body=render_template(
            'email/new_comment.html',
            post=post,
            comment=comment
        )
    )