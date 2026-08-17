#!/usr/bin/env python3
# ============================================================
# ===== DARKHUB — MAIN SERVER =====
# ============================================================

import os
import json
import time
import uuid
import shutil
import subprocess
import threading
import hashlib
import base64
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_file, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import psutil

# ===== استيراد الوحدات =====
from uploader import Uploader
from executor import Executor
from link_generator import LinkGenerator
from controller import Controller
from logger import Logger
from security import Security

# ===== تهيئة التطبيق =====
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
app.config['SECRET_KEY'] = os.urandom(64)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 ساعة

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ===== تهيئة الوحدات =====
uploader = Uploader()
executor = Executor()
link_generator = LinkGenerator()
controller = Controller()
logger = Logger()
security = Security()

# ===== متغيرات =====
files_data = {}
scripts_data = {}
executions_data = {}
START_TIME = time.time()

# ===== إنشاء المجلدات =====
for dir_name in ['uploads', 'logs', 'scripts', 'temp']:
    os.makedirs(dir_name, exist_ok=True)

# ===== المسارات الرئيسية =====

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/files')
def files_page():
    return render_template('files.html')

@app.route('/execute')
def execute_page():
    return render_template('execute.html')

@app.route('/logs')
def logs_page():
    return render_template('logs.html')

@app.route('/script/<script_id>')
def script_page(script_id):
    return render_template('execute.html', script_id=script_id)

@app.route('/control/<file_id>')
def control_page(file_id):
    return render_template('dashboard.html', file_id=file_id)

@app.route('/share/<file_id>')
def share_page(file_id):
    return render_template('share.html', file_id=file_id)

# ===== API: رفع الملفات =====

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """رفع ملف جديد"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'لم يتم اختيار ملف'}), 400
        
        file = request.files['file']
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        is_public = request.form.get('is_public', 'false') == 'true'
        is_script = request.form.get('is_script', 'false') == 'true'
        
        if file.filename == '':
            return jsonify({'error': 'لم يتم اختيار ملف'}), 400
        
        # رفع الملف
        result = uploader.upload(file, name, description, is_public, is_script)
        
        if result['success']:
            file_id = result['file_id']
            files_data[file_id] = result
            
            # توليد الروابط
            control_link = link_generator.generate_control_link(file_id)
            execute_link = link_generator.generate_execute_link(file_id) if is_script else None
            download_link = link_generator.generate_download_link(file_id)
            share_link = link_generator.generate_share_link(file_id)
            
            logger.success(f'✅ تم رفع الملف: {result["name"]} (ID: {file_id})')
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'file': result,
                'links': {
                    'control': control_link,
                    'execute': execute_link,
                    'download': download_link,
                    'share': share_link
                },
                'message': 'تم رفع الملف بنجاح'
            })
        
        logger.error(f'❌ فشل رفع الملف: {result.get("error", "خطأ غير معروف")}')
        return jsonify({'error': result.get('error', 'فشل رفع الملف')}), 400
        
    except Exception as e:
        logger.error(f'❌ خطأ في رفع الملف: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ===== API: الحصول على الملفات =====

@app.route('/api/files', methods=['GET'])
def get_files():
    """الحصول على قائمة الملفات"""
    try:
        files = list(files_data.values())
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """الحصول على ملف محدد"""
    try:
        if file_id not in files_data:
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        return jsonify({
            'success': True,
            'file': files_data[file_id]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API: تنزيل الملف =====

@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """تنزيل ملف"""
    try:
        if file_id not in files_data:
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        file_data = files_data[file_id]
        file_path = file_data['path']
        file_name = file_data['original_name']
        
        # تحديث عدد التنزيلات
        files_data[file_id]['downloads'] = files_data[file_id].get('downloads', 0) + 1
        
        logger.info(f'📥 تنزيل الملف: {file_name} (ID: {file_id})')
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f'❌ فشل تنزيل الملف: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ===== API: حذف الملف =====

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """حذف ملف"""
    try:
        if file_id not in files_data:
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        # حذف الملف الفعلي
        file_path = files_data[file_id]['path']
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # حذف المجلد إذا كان فارغاً
        file_dir = os.path.dirname(file_path)
        if os.path.exists(file_dir) and not os.listdir(file_dir):
            os.rmdir(file_dir)
        
        file_name = files_data[file_id]['name']
        del files_data[file_id]
        
        logger.success(f'🗑️ تم حذف الملف: {file_name} (ID: {file_id})')
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الملف بنجاح'
        })
        
    except Exception as e:
        logger.error(f'❌ فشل حذف الملف: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ===== API: تشغيل الإسكربت =====

@app.route('/api/execute/<file_id>', methods=['POST'])
def execute_script(file_id):
    """تشغيل إسكربت"""
    try:
        if file_id not in files_data:
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        if not files_data[file_id].get('is_script', False):
            return jsonify({'error': 'الملف ليس إسكربتاً'}), 400
        
        # تنفيذ الإسكربت
        result = executor.execute(file_id, files_data[file_id])
        
        if result['success']:
            execution_id = result['execution_id']
            executions_data[execution_id] = result
            
            # تحديث عدد التشغيلات
            files_data[file_id]['executions'] = files_data[file_id].get('executions', 0) + 1
            
            logger.success(f'▶️ تم تشغيل الإسكربت: {files_data[file_id]["name"]} (ID: {file_id})')
            
            # إرسال عبر WebSocket
            socketio.emit('execution_result', {
                'file_id': file_id,
                'execution_id': execution_id,
                'status': 'started'
            })
            
            return jsonify({
                'success': True,
                'execution_id': execution_id,
                'message': 'تم بدء تشغيل الإسكربت'
            })
        
        logger.error(f'❌ فشل تشغيل الإسكربت: {result.get("error", "خطأ غير معروف")}')
        return jsonify({'error': result.get('error', 'فشل تشغيل الإسكربت')}), 400
        
    except Exception as e:
        logger.error(f'❌ خطأ في تشغيل الإسكربت: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ===== API: حالة التشغيل =====

@app.route('/api/execution/<execution_id>', methods=['GET'])
def get_execution(execution_id):
    """الحصول على حالة التشغيل"""
    try:
        if execution_id not in executions_data:
            return jsonify({'error': 'التشغيل غير موجود'}), 404
        
        return jsonify({
            'success': True,
            'execution': executions_data[execution_id]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API: السجلات =====

@app.route('/api/logs/<file_id>', methods=['GET'])
def get_file_logs(file_id):
    """الحصول على سجلات الملف"""
    try:
        logs = executor.get_logs(file_id)
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API: الروابط =====

@app.route('/api/links/<file_id>', methods=['GET'])
def get_links(file_id):
    """الحصول على روابط الملف"""
    try:
        if file_id not in files_data:
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        is_script = files_data[file_id].get('is_script', False)
        
        return jsonify({
            'success': True,
            'links': {
                'control': link_generator.generate_control_link(file_id),
                'execute': link_generator.generate_execute_link(file_id) if is_script else None,
                'download': link_generator.generate_download_link(file_id),
                'share': link_generator.generate_share_link(file_id),
                'short': link_generator.generate_short_link(file_id)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API: التحكم =====

@app.route('/api/control/<file_id>/<action>', methods=['POST'])
def control_action(file_id, action):
    """تنفيذ أمر تحكم"""
    try:
        if file_id not in files_data:
            return jsonify({'error': 'الملف غير موجود'}), 404
        
        params = request.json or {}
        result = controller.execute_action(file_id, action, params)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'تم تنفيذ الأمر {action}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API: حالة النظام =====

@app.route('/api/status', methods=['GET'])
def system_status():
    """حالة النظام"""
    return jsonify({
        'success': True,
        'status': {
            'files': len(files_data),
            'scripts': sum(1 for f in files_data.values() if f.get('is_script', False)),
            'executions': len(executions_data),
            'uptime': time.time() - START_TIME,
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }
    })

# ===== WebSocket =====

@socketio.on('connect')
def handle_connect():
    logger.info(f'🔌 عميل متصل: {request.sid}')
    emit('connected', {'message': '✅ متصل بخادم DARKHUB'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'🔌 عميل غير متصل: {request.sid}')

@socketio.on('execute_script')
def handle_execute(data):
    file_id = data.get('file_id')
    if file_id and file_id in files_data:
        result = executor.execute(file_id, files_data[file_id])
        emit('execution_result', result)

@socketio.on('get_logs')
def handle_get_logs(data):
    file_id = data.get('file_id')
    if file_id:
        logs = executor.get_logs(file_id)
        emit('logs_data', {'logs': logs})

@socketio.on('control_command')
def handle_control(data):
    file_id = data.get('file_id')
    action = data.get('action')
    params = data.get('params', {})
    
    if file_id and file_id in files_data:
        result = controller.execute_action(file_id, action, params)
        emit('control_result', {
            'file_id': file_id,
            'action': action,
            'result': result
        })

# ===== معالجة الأخطاء =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'المسار غير موجود'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'❌ خطأ داخلي: {error}')
    return jsonify({'error': 'خطأ داخلي في الخادم'}), 500

# ===== تشغيل الخادم =====

if __name__ == '__main__':
    # إنشاء المجلدات
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('scripts', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    print('========================================')
    print('🐙 DARKHUB — منصة رفع وربط الإسكربتات')
    print(f'📡 الخادم يعمل على http://localhost:{port}')
    print('📂 مجلد الرفع: ./uploads')
    print('📋 مجلد السجلات: ./logs')
    print('========================================')
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True)