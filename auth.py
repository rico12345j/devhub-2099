#!/usr/bin/env python3
# ============================================================
# ===== RENDER CLONE — AUTH SYSTEM =====
# ===== Version: ULTIMATE | D4 Architecture =====
# ============================================================

from flask import Blueprint, request, jsonify, session
import hashlib
import json
import os
import re
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# ===== ملف المستخدمين =====
USERS_FILE = './users.json'

# ===== دوال مساعدة =====
def load_users():
    """تحميل المستخدمين من الملف"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """حفظ المستخدمين إلى الملف"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# ===== متغيرات =====
users = load_users()

# ===== المسارات =====

@auth_bp.route('/login', methods=['POST'])
def login():
    """تسجيل الدخول"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'اسم المستخدم وكلمة المرور مطلوبان'
        }), 400
    
    hashed = hash_password(password)
    
    if username in users and users[username]['password'] == hashed:
        session['user'] = username
        session['login_time'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الدخول بنجاح',
            'user': username,
            'email': users[username].get('email', '')
        })
    
    return jsonify({
        'success': False,
        'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'
    }), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """تسجيل الخروج"""
    session.pop('user', None)
    session.pop('login_time', None)
    return jsonify({
        'success': True,
        'message': 'تم تسجيل الخروج بنجاح'
    })

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """إنشاء حساب جديد"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    
    if not username or not password or not email:
        return jsonify({
            'success': False,
            'message': 'جميع الحقول مطلوبة'
        }), 400
    
    if len(username) < 3:
        return jsonify({
            'success': False,
            'message': 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل'
        }), 400
    
    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
        }), 400
    
    if not validate_email(email):
        return jsonify({
            'success': False,
            'message': 'البريد الإلكتروني غير صالح'
        }), 400
    
    if username in users:
        return jsonify({
            'success': False,
            'message': 'اسم المستخدم موجود بالفعل'
        }), 400
    
    # إنشاء المستخدم
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'created_at': datetime.now().isoformat(),
        'role': 'user'
    }
    save_users(users)
    
    # تسجيل الدخول تلقائياً
    session['user'] = username
    
    return jsonify({
        'success': True,
        'message': 'تم إنشاء الحساب بنجاح',
        'user': username
    })

@auth_bp.route('/user', methods=['GET'])
def get_user():
    """الحصول على معلومات المستخدم الحالي"""
    if session.get('user'):
        username = session['user']
        return jsonify({
            'success': True,
            'user': username,
            'email': users.get(username, {}).get('email', ''),
            'login_time': session.get('login_time', '')
        })
    
    return jsonify({
        'success': False,
        'message': 'غير مسجل'
    }), 401

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """التحقق من حالة المصادقة"""
    if session.get('user'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': session['user']
        })
    
    return jsonify({
        'success': True,
        'authenticated': False
    })

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """تغيير كلمة المرور"""
    if not session.get('user'):
        return jsonify({
            'success': False,
            'message': 'غير مصرح'
        }), 401
    
    data = request.json
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not old_password or not new_password:
        return jsonify({
            'success': False,
            'message': 'كلمة المرور القديمة والجديدة مطلوبة'
        }), 400
    
    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'message': 'كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل'
        }), 400
    
    username = session['user']
    hashed_old = hash_password(old_password)
    
    if users[username]['password'] != hashed_old:
        return jsonify({
            'success': False,
            'message': 'كلمة المرور القديمة غير صحيحة'
        }), 401
    
    users[username]['password'] = hash_password(new_password)
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': 'تم تغيير كلمة المرور بنجاح'
    })

@auth_bp.route('/users', methods=['GET'])
def get_users():
    """الحصول على قائمة المستخدمين (للمطورين)"""
    # يمكن إضافة صلاحيات هنا
    return jsonify({
        'success': True,
        'users': list(users.keys())
    })