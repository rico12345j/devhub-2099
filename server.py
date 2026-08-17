#!/usr/bin/env python3
# ============================================================
# ===== RENDER CLONE — MAIN SERVER =====
# ============================================================

import os
import json
import time
import uuid
import shutil
import subprocess
import threading
from datetime import datetime
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import psutil
import requests

# ===== استيراد الوحدات =====
from auth import auth_bp
from databases import databases_bp
from deployer import deployer_bp
from logs import logs_bp
from services import services_bp

# ===== تهيئة التطبيق =====
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 ساعة
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ===== إنشاء المجلدات =====
for d in ['./services', './databases', './logs', './domains', './uploads']:
    os.makedirs(d, exist_ok=True)

# ===== تسجيل الـ Blueprints =====
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(deployer_bp, url_prefix='/api/deploy')
app.register_blueprint(services_bp, url_prefix='/api/services')
app.register_blueprint(databases_bp, url_prefix='/api/databases')
app.register_blueprint(logs_bp, url_prefix='/api/logs')

# ===== المسارات الرئيسية =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/services')
def services_page():
    if not session.get('user'):
        return redirect('/login')
    return render_template('services.html')

@app.route('/deploy')
def deploy_page():
    if not session.get('user'):
        return redirect('/login')
    return render_template('deploy.html')

@app.route('/service/<service_id>')
def service_detail(service_id):
    if not session.get('user'):
        return redirect('/login')
    return render_template('service-detail.html', service_id=service_id)

@app.route('/logs/<service_id>')
def logs_page(service_id):
    if not session.get('user'):
        return redirect('/login')
    return render_template('logs.html', service_id=service_id)

@app.route('/settings')
def settings_page():
    if not session.get('user'):
        return redirect('/login')
    return render_template('settings.html')

@app.route('/login')
def login_page():
    if session.get('user'):
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if session.get('user'):
        return redirect('/dashboard')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# ===== API: حالة النظام =====
@app.route('/api/status')
def system_status():
    # تحميل الخدمات
    from deployer import services_data
    from databases import databases_data
    
    return jsonify({
        'success': True,
        'status': {
            'services': len(services_data),
            'databases': len(databases_data),
            'uptime': time.time() - start_time,
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }
    })

# ===== WebSocket =====
@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': '✅ متصل بخادم Render Clone'})

@socketio.on('service-update')
def handle_service_update(data):
    from deployer import services_data
    service_id = data.get('service_id')
    if service_id in services_data:
        emit('service-updated', {
            'service_id': service_id,
            'service': services_data[service_id]
        })

# ===== المتغيرات العالمية =====
start_time = time.time()

# ===== تشغيل الخادم =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('========================================')
    print('☁️ RENDER CLONE')
    print('🚀 نسخة طبق الأصل من Render')
    print(f'📡 الخادم يعمل على http://localhost:{port}')
    print('========================================')
    socketio.run(app, host='0.0.0.0', port=port, debug=True)