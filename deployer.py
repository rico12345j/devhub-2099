#!/usr/bin/env python3
# ============================================================
# ===== RENDER CLONE — DEPLOYER ENGINE =====
# ============================================================

from flask import Blueprint, request, jsonify, session
import uuid
import os
import json
import time
import threading
import subprocess
from datetime import datetime

deployer_bp = Blueprint('deployer', __name__)

# ===== متغيرات =====
SERVICES_DIR = './services'
LOGS_DIR = './logs'
SERVICES_FILE = './services.json'
services_data = {}

# ===== دوال مساعدة =====
def load_services():
    """تحميل الخدمات من الملف"""
    global services_data
    if os.path.exists(SERVICES_FILE):
        try:
            with open(SERVICES_FILE, 'r') as f:
                services_data = json.load(f)
        except:
            services_data = {}
    return services_data

def save_services():
    """حفظ الخدمات إلى الملف"""
    with open(SERVICES_FILE, 'w') as f:
        json.dump(services_data, f, indent=2)

# ===== تحميل البيانات =====
load_services()

# ===== دالة النشر =====
def deploy_service_thread(service_id, data):
    """عملية النشر في الخلفية"""
    service = services_data[service_id]
    service['status'] = 'building'
    save_services()
    
    logs = []
    logs.append(f'[{datetime.now()}] 🚀 بدء بناء {service["name"]}')
    
    # محاكاة خطوات البناء
    steps = [
        ('📦 جلب الكود من المستودع', 2),
        ('🔨 تثبيت الاعتماديات', 3),
        ('⚙️ تكوين البيئة', 2),
        ('🏗️ بناء التطبيق', 3),
        ('📦 تجهيز الحزمة', 2)
    ]
    
    for step, duration in steps:
        logs.append(f'[{datetime.now()}] {step}')
        time.sleep(duration)
        service['progress'] = int((len(logs) / (len(steps) + 1)) * 100)
    
    logs.append(f'[{datetime.now()}] ✅ اكتمل البناء بنجاح')
    
    service['status'] = 'running'
    service['health'] = 'healthy'
    service['progress'] = 100
    service['deployed_at'] = datetime.now().isoformat()
    save_services()
    
    # حفظ السجلات
    log_file = f'{LOGS_DIR}/{service_id}.log'
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(log_file, 'w') as f:
        f.write('\n'.join(logs))

# ===== المسارات =====

@deployer_bp.route('/', methods=['POST'])
def deploy():
    """نشر خدمة جديدة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    data = request.json
    name = data.get('name', '').strip()
    runtime = data.get('runtime', 'python')
    repo_url = data.get('repo_url', '').strip()
    branch = data.get('branch', 'main')
    env_vars = data.get('env_vars', {})
    
    if not name or not repo_url:
        return jsonify({'error': 'الاسم ورابط المستودع مطلوبان'}), 400
    
    # التحقق من الاسم
    if any(s['name'] == name for s in services_data.values()):
        return jsonify({'error': 'خدمة بنفس الاسم موجودة'}), 400
    
    service_id = str(uuid.uuid4())[:8]
    service_dir = f'{SERVICES_DIR}/{service_id}'
    os.makedirs(service_dir, exist_ok=True)
    
    service = {
        'id': service_id,
        'name': name,
        'runtime': runtime,
        'repo_url': repo_url,
        'branch': branch,
        'env_vars': env_vars,
        'status': 'deploying',
        'progress': 0,
        'created_at': datetime.now().isoformat(),
        'created_by': session['user'],
        'url': f'https://{service_id}.render-clone.onrender.com',
        'health': 'pending'
    }
    
    services_data[service_id] = service
    save_services()
    
    # بدء النشر في الخلفية
    thread = threading.Thread(target=deploy_service_thread, args=(service_id, data))
    thread.start()
    
    return jsonify({
        'success': True,
        'service': service,
        'message': 'تم بدء النشر'
    })

@deployer_bp.route('/status/<service_id>', methods=['GET'])
def deploy_status(service_id):
    """حالة النشر"""
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    return jsonify({
        'success': True,
        'service': services_data[service_id]
    })

@deployer_bp.route('/templates', methods=['GET'])
def get_templates():
    """الحصول على قوالب النشر"""
    templates = {
        'python': {
            'name': 'Python Flask',
            'description': 'تطبيق Flask بسيط',
            'runtime': 'python',
            'build_command': 'pip install -r requirements.txt',
            'start_command': 'gunicorn app:app'
        },
        'node': {
            'name': 'Node.js Express',
            'description': 'تطبيق Express بسيط',
            'runtime': 'node',
            'build_command': 'npm install',
            'start_command': 'node index.js'
        },
        'static': {
            'name': 'Static Site',
            'description': 'موقع ثابت (HTML/CSS/JS)',
            'runtime': 'static',
            'build_command': 'echo "بناء موقع ثابت"',
            'start_command': 'serve -s build'
        }
    }
    
    return jsonify({
        'success': True,
        'templates': templates
    })

@deployer_bp.route('/<service_id>/redeploy', methods=['POST'])
def redeploy(service_id):
    """إعادة نشر خدمة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    # إعادة النشر
    data = services_data[service_id]
    del services_data[service_id]
    save_services()
    
    return deploy()