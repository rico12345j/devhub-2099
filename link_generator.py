#!/usr/bin/env python3
# ============================================================
# ===== DARKHUB — LINK GENERATOR =====
# ============================================================

import base64
import hashlib
import json
import qrcode
import io
from datetime import datetime

class LinkGenerator:
    def __init__(self, base_url='https://darkhub.onrender.com'):
        self.base_url = base_url
        self.link_types = {
            'control': '/control/',
            'execute': '/execute/',
            'download': '/download/',
            'share': '/share/',
            'embed': '/embed/',
            'qr': '/qr/',
            'short': '/s/',
            'api': '/api/',
            'webhook': '/webhook/',
            'stream': '/stream/'
        }
    
    def generate_control_link(self, file_id):
        """توليد رابط التحكم الكامل"""
        return f'{self.base_url}{self.link_types["control"]}{file_id}'
    
    def generate_execute_link(self, file_id):
        """توليد رابط تشغيل الإسكربت"""
        return f'{self.base_url}{self.link_types["execute"]}{file_id}'
    
    def generate_download_link(self, file_id, token=None):
        """توليد رابط تنزيل الملف"""
        if token:
            return f'{self.base_url}{self.link_types["download"]}{file_id}?token={token}'
        return f'{self.base_url}{self.link_types["download"]}{file_id}'
    
    def generate_share_link(self, file_id):
        """توليد رابط مشاركة"""
        return f'{self.base_url}{self.link_types["share"]}{file_id}'
    
    def generate_embed_link(self, file_id):
        """توليد رابط تضمين"""
        return f'{self.base_url}{self.link_types["embed"]}{file_id}'
    
    def generate_qr_link(self, file_id):
        """توليد رابط QR"""
        return f'{self.base_url}{self.link_types["qr"]}{file_id}'
    
    def generate_short_link(self, file_id):
        """توليد رابط مختصر"""
        hash_id = hashlib.md5(file_id.encode()).hexdigest()[:6]
        return f'{self.base_url}{self.link_types["short"]}{hash_id}'
    
    def generate_api_link(self, file_id, action):
        """توليد رابط API"""
        return f'{self.base_url}{self.link_types["api"]}{file_id}/{action}'
    
    def generate_webhook_link(self, file_id):
        """توليد رابط Webhook"""
        return f'{self.base_url}{self.link_types["webhook"]}{file_id}'
    
    def generate_stream_link(self, file_id):
        """توليد رابط دفق"""
        return f'{self.base_url}{self.link_types["stream"]}{file_id}'
    
    def generate_all_links(self, file_id, file_name=None):
        """توليد جميع الروابط"""
        return {
            'control': self.generate_control_link(file_id),
            'execute': self.generate_execute_link(file_id),
            'download': self.generate_download_link(file_id),
            'share': self.generate_share_link(file_id),
            'embed': self.generate_embed_link(file_id),
            'qr': self.generate_qr_link(file_id),
            'short': self.generate_short_link(file_id),
            'api': self.generate_api_link(file_id, 'status'),
            'webhook': self.generate_webhook_link(file_id),
            'stream': self.generate_stream_link(file_id)
        }
    
    def generate_qr_code(self, link):
        """توليد رمز QR"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(link)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            return img_io
        except:
            return None
    
    def generate_short_code(self, file_id):
        """توليد كود قصير"""
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=8))
    
    def generate_embed_code(self, file_id, width='100%', height='400'):
        """توليد كود تضمين HTML"""
        embed_link = self.generate_embed_link(file_id)
        return f'''
        <!-- DARKHUB Embed -->
        <iframe src="{embed_link}" 
                width="{width}" 
                height="{height}" 
                frameborder="0" 
                allowfullscreen>
        </iframe>
        '''
    
    def generate_markdown_link(self, file_id, text=None):
        """توليد رابط Markdown"""
        link = self.generate_share_link(file_id)
        if text:
            return f'[{text}]({link})'
        return f'[DARKHUB File]({link})'
    
    def generate_html_button(self, file_id, text='Open File'):
        """توليد زر HTML"""
        link = self.generate_share_link(file_id)
        return f'<a href="{link}" class="darkhub-button">{text}</a>'