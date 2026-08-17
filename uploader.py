#!/usr/bin/env python3
# ============================================================
# ===== DARKHUB — UPLOADER =====
# ============================================================

import os
import uuid
import shutil
import hashlib
import json
import mimetypes
from datetime import datetime

class Uploader:
    def __init__(self, upload_dir='uploads'):
        self.upload_dir = upload_dir
        self.max_size = 1024 * 1024 * 1024  # 1GB
        self.allowed_extensions = {
            # النصوص والكود
            '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.java', '.go', '.rs', '.rb',
            '.pl', '.pm', '.php', '.lua', '.r', '.swift', '.kt', '.scala',
            '.ts', '.jsx', '.tsx', '.vue', '.svelte',
            
            # الأرشيف
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
            
            # الصور
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
            
            # الفيديو
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            
            # الصوت
            '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma',
            
            # المستندات
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.odt', '.ods', '.odp', '.rtf', '.md', '.tex',
            
            # التنفيذيات
            '.exe', '.msi', '.app', '.deb', '.rpm', '.dmg',
            
            # أخرى
            '.iso', '.img', '.bin', '.hex', '.elf'
        }
        
        # إنشاء المجلد
        os.makedirs(upload_dir, exist_ok=True)
    
    def upload(self, file, name='', description='', is_public=True, is_script=False):
        """رفع ملف"""
        try:
            # توليد معرف فريد
            file_id = str(uuid.uuid4())[:8]
            
            # الحصول على اسم الملف الأصلي
            original_name = file.filename
            if not name:
                name = original_name
            
            # الحصول على حجم الملف
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            
            # التحقق من الحجم
            if size > self.max_size:
                return {
                    'success': False,
                    'error': f'حجم الملف كبير جداً (الحد الأقصى: {self.max_size // (1024*1024)}MB)'
                }
            
            # التحقق من نوع الملف
            extension = os.path.splitext(original_name)[1].lower()
            if extension not in self.allowed_extensions:
                return {
                    'success': False,
                    'error': f'نوع الملف غير مدعوم: {extension}'
                }
            
            # إنشاء مجلد الملف
            file_dir = f'{self.upload_dir}/{file_id}'
            os.makedirs(file_dir, exist_ok=True)
            
            # حفظ الملف
            file_path = f'{file_dir}/{original_name}'
            file.save(file_path)
            
            # حساب التشفير
            file_hash = self.hash_file(file_path)
            
            # الحصول على نوع MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # بيانات الملف
            file_data = {
                'id': file_id,
                'name': name,
                'original_name': original_name,
                'path': file_path,
                'size': size,
                'size_human': self.format_size(size),
                'hash': file_hash,
                'mime_type': mime_type or 'application/octet-stream',
                'extension': extension,
                'description': description,
                'is_public': is_public,
                'is_script': is_script,
                'created_at': datetime.now().isoformat(),
                'downloads': 0,
                'executions': 0,
                'views': 0
            }
            
            # حفظ البيانات الوصفية
            metadata_path = f'{file_dir}/metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'file_id': file_id,
                **file_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def hash_file(self, file_path, algorithm='sha256'):
        """حساب هاش الملف"""
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def get_file_info(self, file_id):
        """الحصول على معلومات الملف"""
        metadata_path = f'{self.upload_dir}/{file_id}/metadata.json'
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def update_file_info(self, file_id, data):
        """تحديث معلومات الملف"""
        metadata_path = f'{self.upload_dir}/{file_id}/metadata.json'
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    current = json.load(f)
                current.update(data)
                current['updated_at'] = datetime.now().isoformat()
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=2, ensure_ascii=False)
                return True
            except:
                return False
        return False
    
    def delete_file(self, file_id):
        """حذف ملف"""
        file_dir = f'{self.upload_dir}/{file_id}'
        if os.path.exists(file_dir):
            shutil.rmtree(file_dir)
            return True
        return False
    
    def list_files(self, filter_script=None, filter_public=None):
        """الحصول على قائمة الملفات"""
        files = []
        for item in os.listdir(self.upload_dir):
            item_path = os.path.join(self.upload_dir, item)
            if os.path.isdir(item_path):
                metadata_path = f'{item_path}/metadata.json'
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                            if filter_script is not None and file_data.get('is_script') != filter_script:
                                continue
                            if filter_public is not None and file_data.get('is_public') != filter_public:
                                continue
                            files.append(file_data)
                    except:
                        continue
        return files
    
    def get_stats(self):
        """الحصول على إحصائيات"""
        total_files = 0
        total_size = 0
        script_count = 0
        
        for item in os.listdir(self.upload_dir):
            item_path = os.path.join(self.upload_dir, item)
            if os.path.isdir(item_path):
                metadata_path = f'{item_path}/metadata.json'
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            total_files += 1
                            total_size += data.get('size', 0)
                            if data.get('is_script', False):
                                script_count += 1
                    except:
                        continue
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_human': self.format_size(total_size),
            'script_count': script_count,
            'upload_dir': self.upload_dir
        }
    
    def format_size(self, bytes):
        """تنسيق الحجم"""
        if bytes == 0:
            return '0 B'
        k = 1024
        sizes = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes >= k and i < len(sizes) - 1:
            bytes /= k
            i += 1
        return f'{bytes:.2f} {sizes[i]}'