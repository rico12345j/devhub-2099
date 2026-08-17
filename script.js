// ============================================================
// ===== RENDER CLONE — MAIN SCRIPT =====
// ============================================================

// ===== التهيئة =====
document.addEventListener('DOMContentLoaded', function() {
    loadStatus();
    setInterval(loadStatus, 5000);
    checkAuth();
});

// ===== تحميل حالة النظام =====
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.success) {
            const status = data.status;
            
            const elements = {
                'servicesCount': status.services,
                'memoryUsage': status.memory + '%',
                'cpuUsage': status.cpu + '%'
            };
            
            for (const [id, value] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            }
            
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

// ===== التحقق من المصادقة =====
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/check');
        const data = await response.json();
        
        if (data.success && data.authenticated) {
            const navRight = document.getElementById('navRight');
            if (navRight) {
                navRight.innerHTML = `
                    <span style="color: var(--text-secondary);">👤 ${data.user}</span>
                    <button class="btn btn-outline" onclick="logout()">تسجيل الخروج</button>
                `;
            }
        }
    } catch (error) {
        console.error('❌ فشل التحقق:', error);
    }
}

// ===== تسجيل الدخول =====
async function login() {
    const username = document.getElementById('username')?.value;
    const password = document.getElementById('password')?.value;
    
    if (!username || !password) {
        alert('يرجى إدخال اسم المستخدم وكلمة المرور');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            alert(data.message || 'فشل تسجيل الدخول');
        }
    } catch (error) {
        alert('حدث خطأ أثناء تسجيل الدخول');
    }
}

// ===== التسجيل =====
async function signup() {
    const username = document.getElementById('signupUsername')?.value;
    const email = document.getElementById('signupEmail')?.value;
    const password = document.getElementById('signupPassword')?.value;
    const confirm = document.getElementById('signupConfirm')?.value;
    
    if (!username || !email || !password) {
        alert('يرجى ملء جميع الحقول');
        return;
    }
    
    if (password !== confirm) {
        alert('كلمات المرور غير متطابقة');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ تم إنشاء الحساب بنجاح');
            window.location.href = '/dashboard';
        } else {
            alert(data.message || 'فشل إنشاء الحساب');
        }
    } catch (error) {
        alert('حدث خطأ أثناء إنشاء الحساب');
    }
}

// ===== تسجيل الخروج =====
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        console.error('❌ فشل تسجيل الخروج:', error);
    }
}

// ===== نشر تطبيق =====
async function deployApp() {
    const name = document.getElementById('appName')?.value;
    const repo = document.getElementById('repoUrl')?.value;
    const runtime = document.getElementById('runtime')?.value || 'python';
    
    if (!name || !repo) {
        alert('يرجى إدخال اسم التطبيق ورابط المستودع');
        return;
    }
    
    try {
        const response = await fetch('/api/deploy/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, repo_url: repo, runtime })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ تم بدء نشر التطبيق ${name}\n📡 الرابط: ${data.service.url}`);
            window.location.href = '/services';
        } else {
            alert(`❌ فشل النشر: ${data.error}`);
        }
    } catch (error) {
        alert('❌ حدث خطأ أثناء النشر');
    }
}

// ===== إيقاف خدمة =====
async function stopService(serviceId) {
    if (!confirm('⛔ هل أنت متأكد من إيقاف هذه الخدمة؟')) return;
    
    try {
        const response = await fetch(`/api/services/${serviceId}/stop`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('✅ تم إيقاف الخدمة');
            location.reload();
        }
    } catch (error) {
        alert('❌ فشل إيقاف الخدمة');
    }
}

// ===== تشغيل خدمة =====
async function startService(serviceId) {
    try {
        const response = await fetch(`/api/services/${serviceId}/start`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('✅ تم تشغيل الخدمة');
            location.reload();
        }
    } catch (error) {
        alert('❌ فشل تشغيل الخدمة');
    }
}

// ===== حذف خدمة =====
async function deleteService(serviceId) {
    if (!confirm('🗑️ هل أنت متأكد من حذف هذه الخدمة؟ هذا الإجراء لا يمكن التراجع عنه!')) return;
    
    try {
        const response = await fetch(`/api/services/${serviceId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            alert('✅ تم حذف الخدمة');
            location.reload();
        }
    } catch (error) {
        alert('❌ فشل حذف الخدمة');
    }
}

// ===== تحميل الخدمات =====
async function loadServices() {
    try {
        const response = await fetch('/api/services/');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('servicesList');
            if (!container) return;
            
            if (data.services.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>لا توجد خدمات</p>
                        <button class="btn btn-primary" onclick="window.location.href='/deploy'">
                            نشر خدمة جديدة
                        </button>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = data.services.map(s => `
                <div class="service-item">
                    <div class="service-info">
                        <span class="service-name">${s.name}</span>
                        <span class="service-status ${s.status}">${s.status}</span>
                        <span class="service-url">${s.url}</span>
                        <span class="service-created">${new Date(s.created_at).toLocaleDateString('ar')}</span>
                    </div>
                    <div class="service-actions">
                        <a href="/service/${s.id}" class="btn btn-outline">عرض</a>
                        <a href="/logs/${s.id}" class="btn btn-outline">📋 سجلات</a>
                        ${s.status === 'running' ? 
                            `<button onclick="stopService('${s.id}')" class="btn btn-danger">⛔ إيقاف</button>` :
                            `<button onclick="startService('${s.id}')" class="btn btn-primary">▶ تشغيل</button>`
                        }
                        <button onclick="deleteService('${s.id}')" class="btn btn-danger">🗑️ حذف</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('❌ فشل تحميل الخدمات:', error);
    }
}

// ===== تصدير الدوال =====
window.login = login;
window.signup = signup;
window.logout = logout;
window.deployApp = deployApp;
window.stopService = stopService;
window.startService = startService;
window.deleteService = deleteService;
window.loadServices = loadServices;
window.loadLogs = loadLogs;