// ============================================================
// ===== DARKHUB — MAIN SCRIPT =====
// ============================================================

// ===== التهيئة =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🐙 DARKHUB — جاهز');
    
    loadStatus();
    setInterval(loadStatus, 5000);
    initWebSocket();
    initDarkMode();
});

// ===== تحميل حالة النظام =====
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.success) {
            const status = data.status;
            
            // تحديث الإحصائيات
            const elements = {
                'filesCount': status.files || 0,
                'scriptsCount': status.scripts || 0,
                'executionsCount': status.executions || 0
            };
            
            for (const [id, value] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            }
            
            // تحديث وقت التشغيل
            if (status.uptime) {
                const seconds = Math.floor(status.uptime);
                const hours = String(Math.floor(seconds / 3600)).padStart(2, '0');
                const minutes = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
                const secs = String(seconds % 60).padStart(2, '0');
                const el = document.getElementById('uptime');
                if (el) el.textContent = `${hours}:${minutes}:${secs}`;
            }
        }
    } catch (error) {
        console.error('❌ فشل تحميل الحالة:', error);
    }
}

// ===== WebSocket =====
function initWebSocket() {
    try {
        const socket = io();
        
        socket.on('connect', function() {
            console.log('✅ متصل بخادم DARKHUB');
        });
        
        socket.on('disconnect', function() {
            console.log('❌ غير متصل بالخادم');
        });
        
        socket.on('connected', function(data) {
            console.log('✅', data.message);
        });
        
        socket.on('execution_result', function(data) {
            console.log('📊 نتيجة التشغيل:', data);
            if (data.success) {
                showNotification('✅ تم تشغيل الإسكربت بنجاح', 'success');
            } else {
                showNotification('❌ فشل تشغيل الإسكربت: ' + (data.error || 'خطأ غير معروف'), 'error');
            }
        });
        
        socket.on('logs_data', function(data) {
            console.log('📋 السجلات:', data.logs);
        });
        
        socket.on('control_result', function(data) {
            console.log('🎮 نتيجة التحكم:', data);
            showNotification(`✅ تم تنفيذ الأمر: ${data.action}`, 'success');
        });
        
        return socket;
    } catch (error) {
        console.error('❌ فشل تهيئة WebSocket:', error);
        return null;
    }
}

// ===== رفع ملف =====
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const nameInput = document.getElementById('fileNameInput');
    const descInput = document.getElementById('fileDesc');
    const isScript = document.getElementById('isScript')?.checked || false;
    
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showNotification('⚠️ يرجى اختيار ملف', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', nameInput?.value || file.name);
    formData.append('description', descInput?.value || '');
    formData.append('is_public', 'true');
    formData.append('is_script', isScript ? 'true' : 'false');
    
    // إظهار شريط التقدم
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('uploadProgressBar');
    const progressText = document.getElementById('uploadProgressText');
    if (progressDiv) progressDiv.style.display = 'block';
    
    try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);
        
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable && progressBar && progressText) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percent + '%';
                progressText.textContent = percent + '%';
            }
        };
        
        xhr.onload = function() {
            const data = JSON.parse(xhr.responseText);
            
            if (data.success) {
                showNotification('✅ تم رفع الملف بنجاح!', 'success');
                
                // عرض الروابط
                const resultDiv = document.getElementById('uploadResult');
                if (resultDiv) {
                    resultDiv.style.display = 'block';
                    document.getElementById('controlLink').value = data.links.control;
                    document.getElementById('executeLink').value = data.links.execute || 'غير متاح';
                    document.getElementById('downloadLink').value = data.links.download;
                }
                
                // إعادة تعيين النموذج
                if (fileInput) fileInput.value = '';
                if (nameInput) nameInput.value = '';
                if (descInput) descInput.value = '';
                if (progressDiv) progressDiv.style.display = 'none';
                
            } else {
                showNotification('❌ فشل الرفع: ' + (data.error || 'خطأ غير معروف'), 'error');
                if (progressDiv) progressDiv.style.display = 'none';
            }
        };
        
        xhr.onerror = function() {
            showNotification('❌ خطأ في الاتصال بالخادم', 'error');
            if (progressDiv) progressDiv.style.display = 'none';
        };
        
        xhr.send(formData);
        
    } catch (error) {
        showNotification('❌ خطأ: ' + error.message, 'error');
        if (progressDiv) progressDiv.style.display = 'none';
    }
}

// ===== نسخ النص =====
function copyText(elementId) {
    const input = document.getElementById(elementId);
    if (!input) return;
    
    input.select();
    try {
        document.execCommand('copy');
        showNotification('📋 تم نسخ الرابط', 'success');
    } catch (e) {
        // محاولة بديلة
        navigator.clipboard.writeText(input.value).then(() => {
            showNotification('📋 تم نسخ الرابط', 'success');
        }).catch(() => {
            showNotification('❌ فشل نسخ الرابط', 'error');
        });
    }
}

// ===== حذف ملف =====
async function deleteFile(fileId) {
    if (!confirm('🗑️ هل أنت متأكد من حذف هذا الملف؟')) return;
    
    try {
        const response = await fetch(`/api/files/${fileId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ تم حذف الملف', 'success');
            location.reload();
        } else {
            showNotification('❌ فشل الحذف: ' + (data.error || 'خطأ غير معروف'), 'error');
        }
    } catch (error) {
        showNotification('❌ خطأ: ' + error.message, 'error');
    }
}

// ===== تشغيل إسكربت =====
async function executeScript(fileId) {
    if (!confirm('⚠️ هل أنت متأكد من تشغيل هذا الإسكربت؟')) return;
    
    try {
        const response = await fetch(`/api/execute/${fileId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ تم تشغيل الإسكربت بنجاح', 'success');
            // عرض المخرجات
            const output = document.getElementById('outputContainer');
            if (output && data.output) {
                output.innerHTML = data.output.split('\n').map(line => 
                    `<div class="output-line">> ${line}</div>`
                ).join('');
            }
        } else {
            showNotification('❌ فشل التشغيل: ' + (data.error || 'خطأ غير معروف'), 'error');
        }
    } catch (error) {
        showNotification('❌ خطأ: ' + error.message, 'error');
    }
}

// ===== الإشعارات =====
function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer') || createNotificationContainer();
    
    const colors = {
        success: '#3fb950',
        error: '#f85149',
        warning: '#d29922',
        info: '#4a9eff'
    };
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    const notification = document.createElement('div');
    notification.className = `notification-toast ${type}`;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #14141f;
        border: 1px solid ${colors[type]};
        color: #ffffff;
        padding: 12px 20px;
        border-radius: 8px;
        font-family: 'Inter', 'Cairo', sans-serif;
        font-size: 14px;
        z-index: 9999;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        max-width: 400px;
        animation: slideIn 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    notification.innerHTML = `<span>${icons[type] || 'ℹ️'}</span> ${message}`;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(20px)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notificationContainer';
    container.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 8px;
    `;
    document.body.appendChild(container);
    return container;
}

// ===== الوضع الليلي =====
function initDarkMode() {
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        document.body.classList.add('dark-mode');
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
    showNotification(
        document.body.classList.contains('dark-mode') ? '🌙 الوضع الليلي مفعّل' : '☀️ الوضع النهاري مفعّل',
        'info'
    );
}

// ===== تصدير الدوال =====
window.uploadFile = uploadFile;
window.deleteFile = deleteFile;
window.executeScript = executeScript;
window.copyText = copyText;
window.toggleDarkMode = toggleDarkMode;
window.showNotification = showNotification;

// ===== إضافة أنيميشن CSS =====
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
`;
document.head.appendChild(style);

console.log('🐙 DARKHUB — جاهز للاستخدام');