#!/usr/bin/env python3
# ============================================================
# ===== DARKHUB — LOGGER =====
# ============================================================

import os
import json
import time
from datetime import datetime

class Logger:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_levels = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3,
            'CRITICAL': 4,
            'SUCCESS': 5
        }
        self.current_level = 'INFO'
    
    def log(self, level, message, data=None):
        """تسجيل رسالة"""
        if self.log_levels.get(level, 0) < self.log_levels.get(self.current_level, 0):
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'data': data,
            'pid': os.getpid()
        }
        
        # تسجيل إلى الملف
        log_file = f'{self.log_dir}/{datetime.now().strftime("%Y-%m-%d")}.log'
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # تسجيل إلى الكونسول
        colors = {
            'DEBUG': '\033[36m',
            'INFO': '\033[32m',
            'WARNING': '\033[33m',
            'ERROR': '\033[31m',
            'CRITICAL': '\033[41m',
            'SUCCESS': '\033[32m'
        }
        color = colors.get(level, '\033[0m')
        print(f'{color}[{log_entry["timestamp"]}] [{level}] {message}\033[0m')
    
    def debug(self, message, data=None):
        self.log('DEBUG', message, data)
    
    def info(self, message, data=None):
        self.log('INFO', message, data)
    
    def warning(self, message, data=None):
        self.log('WARNING', message, data)
    
    def error(self, message, data=None):
        self.log('ERROR', message, data)
    
    def critical(self, message, data=None):
        self.log('CRITICAL', message, data)
    
    def success(self, message, data=None):
        self.log('SUCCESS', message, data)
    
    def get_logs(self, date=None, level=None, limit=100):
        """الحصول على السجلات"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = f'{self.log_dir}/{date}.log'
        if not os.path.exists(log_file):
            return []
        
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if level and log_entry.get('level') != level:
                        continue
                    logs.append(log_entry)
                except:
                    continue
        
        return logs[-limit:]
    
    def clear_logs(self, date=None):
        """مسح السجلات"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = f'{self.log_dir}/{date}.log'
        if os.path.exists(log_file):
            os.remove(log_file)
            return True
        return False
    
    def get_stats(self):
        """الحصول على إحصائيات السجلات"""
        stats = {
            'total_logs': 0,
            'levels': {},
            'files': []
        }
        
        for file in os.listdir(self.log_dir):
            if file.endswith('.log'):
                file_path = f'{self.log_dir}/{file}'
                with open(file_path, 'r') as f:
                    count = sum(1 for _ in f)
                stats['files'].append({
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'count': count
                })
                stats['total_logs'] += count
        
        return stats