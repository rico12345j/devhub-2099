#!/usr/bin/env python3
# ============================================================
# ===== RENDER CLONE — LOGS MANAGER =====
# ============================================================

from flask import Blueprint, request, jsonify, send_file
import os
from datetime import datetime

logs_bp = Blueprint('logs', __name__)

# ===== متغيرات =====
LOGS_DIR = './logs'

# ===== المسارات =====

@logs_bp.route('/<service_id>', methods=['GET'])
def get_logs(service_id):
    """الحصول على سجلات خدمة"""
    log_file = f'{LOGS_DIR}/{service_id}.log'
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.read().splitlines()
    else:
        logs = ['لا توجد سجلات']
    
    return jsonify({
        'success': True,
        'logs': logs,
        'service_id': service_id,
        'count': len(logs)
    })

@logs_bp.route('/<service_id>/tail', methods=['GET'])
def tail_logs(service_id):
    """الحصول على آخر 50 سطراً من السجلات"""
    log_file = f'{LOGS_DIR}/{service_id}.log'
    lines = request.args.get('lines', 50, type=int)
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            all_logs = f.read().splitlines()
            logs = all_logs[-lines:] if len(all_logs) > lines else all_logs
    else:
        logs = ['لا توجد سجلات']
    
    return jsonify({
        'success': True,
        'logs': logs,
        'service_id': service_id,
        'total': len(logs)
    })

@logs_bp.route('/<service_id>', methods=['POST'])
def add_log(service_id):
    """إضافة سجل جديد"""
    data = request.json
    message = data.get('message', '').strip()
    level = data.get('level', 'info')
    
    if not message:
        return jsonify({'error': 'الرسالة مطلوبة'}), 400
    
    log_file = f'{LOGS_DIR}/{service_id}.log'
    log_entry = f'[{datetime.now()}] [{level.upper()}] {message}'
    
    with open(log_file, 'a') as f:
        f.write(log_entry + '\n')
    
    return jsonify({
        'success': True,
        'message': 'تم إضافة السجل',
        'entry': log_entry
    })

@logs_bp.route('/<service_id>', methods=['DELETE'])
def clear_logs(service_id):
    """مسح سجلات خدمة"""
    log_file = f'{LOGS_DIR}/{service_id}.log'
    
    if os.path.exists(log_file):
        os.remove(log_file)
        return jsonify({
            'success': True,
            'message': 'تم مسح السجلات'
        })
    
    return jsonify({
        'success': False,
        'message': 'لا توجد سجلات'
    }), 404

@logs_bp.route('/<service_id>/download', methods=['GET'])
def download_logs(service_id):
    """تحميل سجلات خدمة"""
    log_file = f'{LOGS_DIR}/{service_id}.log'
    
    if os.path.exists(log_file):
        return send_file(
            log_file,
            as_attachment=True,
            download_name=f'{service_id}_logs_{datetime.now().strftime("%Y%m%d")}.log'
        )
    
    return jsonify({'error': 'لا توجد سجلات'}), 404

@logs_bp.route('/<service_id>/search', methods=['GET'])
def search_logs(service_id):
    """البحث في السجلات"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'نص البحث مطلوب'}), 400
    
    log_file = f'{LOGS_DIR}/{service_id}.log'
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.read().splitlines()
            results = [line for line in logs if query.lower() in line.lower()]
    else:
        results = []
    
    return jsonify({
        'success': True,
        'results': results,
        'count': len(results),
        'query': query
    })