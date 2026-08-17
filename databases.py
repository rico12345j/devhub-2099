#!/usr/bin/env python3
# ============================================================
# ===== RENDER CLONE — DATABASES MANAGER =====
# ============================================================

from flask import Blueprint, request, jsonify, session
import uuid
import os
import json
from datetime import datetime

databases_bp = Blueprint('databases', __name__)

# ===== متغيرات =====
DATABASES_DIR = './databases'
DATABASES_FILE = './databases.json'
databases_data = {}

# ===== دوال مساعدة =====
def load_databases():
    """تحميل قواعد البيانات من الملف"""
    global databases_data
    if os.path.exists(DATABASES_FILE):
        try:
            with open(DATABASES_FILE, 'r') as f:
                databases_data = json.load(f)
        except:
            databases_data = {}
    return databases_data

def save_databases():
    """حفظ قواعد البيانات إلى الملف"""
    with open(DATABASES_FILE, 'w') as f:
        json.dump(databases_data, f, indent=2)

# ===== تحميل البيانات =====
load_databases()

# ===== المسارات =====

@databases_bp.route('/', methods=['GET'])
def get_databases():
    """الحصول على جميع قواعد البيانات"""
    return jsonify({
        'success': True,
        'databases': list(databases_data.values())
    })

@databases_bp.route('/', methods=['POST'])
def create_database():
    """إنشاء قاعدة بيانات جديدة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    data = request.json
    name = data.get('name', '').strip()
    db_type = data.get('type', 'postgresql')
    version = data.get('version', '14')
    
    if not name:
        return jsonify({'error': 'الاسم مطلوب'}), 400
    
    # التحقق من الاسم
    if any(db['name'] == name for db in databases_data.values()):
        return jsonify({'error': 'قاعدة بيانات بنفس الاسم موجودة'}), 400
    
    db_id = str(uuid.uuid4())[:8]
    
    database = {
        'id': db_id,
        'name': name,
        'type': db_type,
        'version': version,
        'status': 'running',
        'created_at': datetime.now().isoformat(),
        'created_by': session['user'],
        'connection_string': f'{db_type}://localhost:5432/{name}',
        'size': '0 MB',
        'tables': 0
    }
    
    databases_data[db_id] = database
    save_databases()
    
    # إنشاء المجلد
    os.makedirs(f'{DATABASES_DIR}/{db_id}', exist_ok=True)
    
    return jsonify({
        'success': True,
        'database': database,
        'message': f'تم إنشاء قاعدة البيانات {name}'
    })

@databases_bp.route('/<db_id>', methods=['GET'])
def get_database(db_id):
    """الحصول على قاعدة بيانات محددة"""
    if db_id not in databases_data:
        return jsonify({'error': 'قاعدة البيانات غير موجودة'}), 404
    
    return jsonify({
        'success': True,
        'database': databases_data[db_id]
    })

@databases_bp.route('/<db_id>', methods=['DELETE'])
def delete_database(db_id):
    """حذف قاعدة بيانات"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if db_id not in databases_data:
        return jsonify({'error': 'قاعدة البيانات غير موجودة'}), 404
    
    db_name = databases_data[db_id]['name']
    del databases_data[db_id]
    save_databases()
    
    # حذف المجلد
    import shutil
    shutil.rmtree(f'{DATABASES_DIR}/{db_id}', ignore_errors=True)
    
    return jsonify({
        'success': True,
        'message': f'تم حذف قاعدة البيانات {db_name}'
    })

@databases_bp.route('/<db_id>/backup', methods=['POST'])
def backup_database(db_id):
    """إنشاء نسخة احتياطية لقاعدة البيانات"""
    if db_id not in databases_data:
        return jsonify({'error': 'قاعدة البيانات غير موجودة'}), 404
    
    # محاكاة إنشاء نسخة احتياطية
    backup_file = f'{DATABASES_DIR}/{db_id}/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
    with open(backup_file, 'w') as f:
        f.write(f'-- نسخة احتياطية لقاعدة البيانات {databases_data[db_id]["name"]}\n')
        f.write(f'-- التاريخ: {datetime.now().isoformat()}\n')
        f.write('CREATE TABLE backup_test (id SERIAL PRIMARY KEY);\n')
    
    return jsonify({
        'success': True,
        'message': 'تم إنشاء النسخة الاحتياطية',
        'file': backup_file
    })

@databases_bp.route('/<db_id>/stats', methods=['GET'])
def database_stats(db_id):
    """إحصائيات قاعدة البيانات"""
    if db_id not in databases_data:
        return jsonify({'error': 'قاعدة البيانات غير موجودة'}), 404
    
    # محاكاة الإحصائيات
    import random
    return jsonify({
        'success': True,
        'stats': {
            'size': f'{random.randint(1, 100)} MB',
            'tables': random.randint(1, 50),
            'rows': random.randint(100, 10000),
            'connections': random.randint(1, 10),
            'uptime': f'{random.randint(1, 24)}h {random.randint(0, 59)}m'
        }
    })