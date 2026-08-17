#!/usr/bin/env python3
# ============================================================
# ===== DARKHUB — EXECUTOR =====
# ============================================================

import os
import sys
import subprocess
import threading
import time
import uuid
import signal
import psutil
from datetime import datetime

class Executor:
    def __init__(self):
        self.executions = {}
        self.running_processes = {}
        self.logs_dir = 'logs'
        os.makedirs(self.logs_dir, exist_ok=True)
        
        self.languages = {
            '.py': {
                'command': ['python3'],
                'extension': '.py',
                'name': 'Python'
            },
            '.js': {
                'command': ['node'],
                'extension': '.js',
                'name': 'Node.js'
            },
            '.sh': {
                'command': ['bash'],
                'extension': '.sh',
                'name': 'Bash'
            },
            '.pl': {
                'command': ['perl'],
                'extension': '.pl',
                'name': 'Perl'
            },
            '.rb': {
                'command': ['ruby'],
                'extension': '.rb',
                'name': 'Ruby'
            },
            '.php': {
                'command': ['php'],
                'extension': '.php',
                'name': 'PHP'
            },
            '.go': {
                'command': ['go', 'run'],
                'extension': '.go',
                'name': 'Go'
            },
            '.rs': {
                'command': ['rustc'],
                'extension': '.rs',
                'name': 'Rust'
            },
            '.c': {
                'command': ['gcc'],
                'extension': '.c',
                'name': 'C'
            },
            '.cpp': {
                'command': ['g++'],
                'extension': '.cpp',
                'name': 'C++'
            },
            '.java': {
                'command': ['javac'],
                'extension': '.java',
                'name': 'Java'
            },
            '.lua': {
                'command': ['lua'],
                'extension': '.lua',
                'name': 'Lua'
            },
            '.r': {
                'command': ['Rscript'],
                'extension': '.r',
                'name': 'R'
            },
            '.swift': {
                'command': ['swift'],
                'extension': '.swift',
                'name': 'Swift'
            },
            '.kt': {
                'command': ['kotlin'],
                'extension': '.kt',
                'name': 'Kotlin'
            },
            '.exe': {
                'command': ['./'],
                'extension': '.exe',
                'name': 'Executable'
            }
        }
    
    def execute(self, file_id, file_data):
        """تنفيذ إسكربت"""
        try:
            execution_id = str(uuid.uuid4())[:8]
            file_path = file_data['path']
            file_name = file_data['name']
            
            # تحديد نوع الملف
            extension = os.path.splitext(file_name)[1].lower()
            lang_config = self.languages.get(extension)
            
            if not lang_config:
                return {
                    'success': False,
                    'error': f'نوع الملف غير مدعوم: {extension}'
                }
            
            # بناء الأمر
            command = lang_config['command'] + [file_path]
            
            # تشغيل في الخلفية
            logs = []
            output = ''
            error = ''
            
            def run():
                nonlocal output, error
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(file_path)
                    )
                    
                    self.running_processes[execution_id] = process
                    
                    stdout, stderr = process.communicate(timeout=300)
                    
                    output = stdout
                    error = stderr
                    
                    if process.returncode == 0:
                        status = 'success'
                    else:
                        status = 'error'
                    
                    # حفظ النتائج
                    self.executions[execution_id] = {
                        'id': execution_id,
                        'file_id': file_id,
                        'file_name': file_name,
                        'status': status,
                        'output': output,
                        'error': error,
                        'return_code': process.returncode,
                        'timestamp': datetime.now().isoformat(),
                        'language': lang_config['name']
                    }
                    
                    # حفظ السجلات
                    log_file = f'{self.logs_dir}/{execution_id}.log'
                    with open(log_file, 'w') as f:
                        f.write(f'=== EXECUTION LOG ===\n')
                        f.write(f'File: {file_name}\n')
                        f.write(f'Language: {lang_config["name"]}\n')
                        f.write(f'Status: {status}\n')
                        f.write(f'Return Code: {process.returncode}\n')
                        f.write(f'Output:\n{output}\n')
                        if error:
                            f.write(f'Error:\n{error}\n')
                    
                    del self.running_processes[execution_id]
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    self.executions[execution_id] = {
                        'id': execution_id,
                        'file_id': file_id,
                        'file_name': file_name,
                        'status': 'timeout',
                        'output': '',
                        'error': 'Execution timeout (300 seconds)',
                        'return_code': -1,
                        'timestamp': datetime.now().isoformat(),
                        'language': lang_config['name']
                    }
                    del self.running_processes[execution_id]
                    
                except Exception as e:
                    self.executions[execution_id] = {
                        'id': execution_id,
                        'file_id': file_id,
                        'file_name': file_name,
                        'status': 'error',
                        'output': '',
                        'error': str(e),
                        'return_code': -1,
                        'timestamp': datetime.now().isoformat(),
                        'language': lang_config['name']
                    }
                    if execution_id in self.running_processes:
                        del self.running_processes[execution_id]
            
            # تشغيل في خيط منفصل
            thread = threading.Thread(target=run)
            thread.start()
            
            return {
                'success': True,
                'execution_id': execution_id,
                'message': f'تم بدء تشغيل الإسكربت ({lang_config["name"]})'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_execution(self, execution_id):
        """الحصول على نتيجة التشغيل"""
        return self.executions.get(execution_id)
    
    def get_logs(self, execution_id):
        """الحصول على سجلات التشغيل"""
        log_file = f'{self.logs_dir}/{execution_id}.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return f.read().splitlines()
        return []
    
    def stop_execution(self, execution_id):
        """إيقاف تشغيل"""
        if execution_id in self.running_processes:
            process = self.running_processes[execution_id]
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            del self.running_processes[execution_id]
            return True
        return False
    
    def get_running(self):
        """الحصول على العمليات الجارية"""
        return list(self.running_processes.keys())
    
    def get_languages(self):
        """الحصول على قائمة اللغات المدعومة"""
        return {ext: config['name'] for ext, config in self.languages.items()}