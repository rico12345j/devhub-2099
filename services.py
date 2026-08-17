#!/usr/bin/env python3
# ============================================================
# ===== RENDER CLONE — SERVICES MANAGER =====
# ============================================================

from flask import Blueprint, request, jsonify, session
import shutil
import os
import json
from datetime import datetime

services_bp = Blueprint('services', __name__)

# ===== متغيرات =====
SERVICES_DIR = './services'
LOGS_DIR = './logs'
SERVICES_FILE = './services.json'

# ===== دوال مساعدة =====
def load_services():
    """تحميل الخدمات من الملف"""
    if os.path.exists(SERVICES_FILE):
        try:
            with open(SERVICES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_services(services_data):
    """حفظ الخدمات إلى الملف"""
    with open(SERVICES_FILE, 'w') as f:
        json.dump(services_data, f, indent=2)

# ===== تحميل البيانات =====
services_data = load_services()

# ===== المسارات =====

@services_bp.route('/', methods=['GET'])
def get_services():
    """الحصول على جميع الخدمات"""
    return jsonify({
        'success': True,
        'services': list(services_data.values())
    })

@services_bp.route('/<service_id>', methods=['GET'])
def get_service(service_id):
    """الحصول على خدمة محددة"""
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    return jsonify({
        'success': True,
        'service': services_data[service_id]
    })

@services_bp.route('/<service_id>', methods=['DELETE'])
def delete_service(service_id):
    """حذف خدمة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    service_name = services_data[service_id]['name']
    
    # حذف المجلدات
    shutil.rmtree(f'{SERVICES_DIR}/{service_id}', ignore_errors=True)
    if os.path.exists(f'{LOGS_DIR}/{service_id}.log'):
        os.remove(f'{LOGS_DIR}/{service_id}.log')
    
    del services_data[service_id]
    save_services(services_data)
    
    return jsonify({
        'success': True,
        'message': f'تم حذف الخدمة {service_name}'
    })

@services_bp.route('/<service_id>/stop', methods=['POST'])
def stop_service(service_id):
    """إيقاف خدمة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    services_data[service_id]['status'] = 'stopped'
    save_services(services_data)
    
    with open(f'{LOGS_DIR}/{service_id}.log', 'a') as f:
        f.write(f'\n[{datetime.now()}] ⛔ تم إيقاف الخدمة')
    
    return jsonify({
        'success': True,
        'message': 'تم إيقاف الخدمة'
    })

@services_bp.route('/<service_id>/start', methods=['POST'])
def start_service(service_id):
    """تشغيل خدمة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    services_data[service_id]['status'] = 'running'
    save_services(services_data)
    
    with open(f'{LOGS_DIR}/{service_id}.log', 'a') as f:
        f.write(f'\n[{datetime.now()}] ▶️ تم تشغيل الخدمة')
    
    return jsonify({
        'success': True,
        'message': 'تم تشغيل الخدمة'
    })

@services_bp.route('/<service_id>/restart', methods=['POST'])
def restart_service(service_id):
    """إعادة تشغيل خدمة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    services_data[service_id]['status'] = 'running'
    save_services(services_data)
    
    with open(f'{LOGS_DIR}/{service_id}.log', 'a') as f:
        f.write(f'\n[{datetime.now()}] 🔄 تم إعادة تشغيل الخدمة')
    
    return jsonify({
        'success': True,
        'message': 'تم إعادة تشغيل الخدمة'
    })

@services_bp.route('/<service_id>/env', methods=['PUT'])
def update_env(service_id):
    """تحديث متغيرات البيئة"""
    if not session.get('user'):
        return jsonify({'error': 'غير مصرح'}), 401
    
    if service_id not in services_data:
        return jsonify({'error': 'الخدمة غير موجودة'}), 404
    
    data = request.json
    env_vars = data.get('env_vars', {})
    
    services_data[service_id]['env_vars'] = env_vars
    save_services(services_data)
    
    return jsonify({
        'success': True,
        'message': 'تم تحديث متغيرات البيئة'
    })