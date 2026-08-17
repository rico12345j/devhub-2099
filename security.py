#!/usr/bin/env python3
# ============================================================
# ===== DARKHUB — SECURITY =====
# ============================================================

import os
import hashlib
import base64
import json
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import jwt
import bcrypt

class Security:
    def __init__(self):
        self.key_file = '.secret.key'
        self.jwt_secret = os.environ.get('JWT_SECRET', 'darkhub-secret-key-2024')
        self.fernet_key = self.get_or_create_key()
        self.cipher = Fernet(self.fernet_key)
    
    def get_or_create_key(self):
        """الحصول على مفتاح التشفير أو إنشائه"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def encrypt(self, data):
        """تشفير البيانات"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """فك تشفير البيانات"""
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_file(self, file_path):
        """تشفير ملف"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.encrypt(data)
        encrypted_path = file_path + '.enc'
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted)
        
        return encrypted_path
    
    def decrypt_file(self, file_path):
        """فك تشفير ملف"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        decrypted = self.decrypt(data)
        decrypted_path = file_path.replace('.enc', '')
        with open(decrypted_path, 'wb') as f:
            f.write(decrypted)
        
        return decrypted_path
    
    def hash_password(self, password):
        """تشفير كلمة المرور"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt)
    
    def verify_password(self, password, hashed):
        """التحقق من كلمة المرور"""
        return bcrypt.checkpw(password.encode(), hashed)
    
    def generate_jwt(self, data, expires_in=3600):
        """توليد JWT"""
        payload = {
            'data': data,
            'exp': time.time() + expires_in
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt(self, token):
        """التحقق من JWT"""
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
        except:
            return None
    
    def hash_file(self, file_path, algorithm='sha256'):
        """حساب هاش الملف"""
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def generate_signature(self, data):
        """توليد توقيع"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_signature(self, data, signature):
        """التحقق من التوقيع"""
        return self.generate_signature(data) == signature
    
    def generate_api_key(self):
        """توليد مفتاح API"""
        return base64.b64encode(os.urandom(32)).decode()
    
    def generate_otp(self, length=6):
        """توليد رمز OTP"""
        import random
        return ''.join(str(random.randint(0, 9)) for _ in range(length))
    
    def rate_limit(self, key, max_requests=100, window=60):
        """التحكم في معدل الطلبات"""
        # يمكن استخدام Redis هنا
        return True
    
    def sanitize_input(self, data):
        """تنظيف المدخلات"""
        if isinstance(data, str):
            return data.replace('<', '&lt;').replace('>', '&gt;')
        return data