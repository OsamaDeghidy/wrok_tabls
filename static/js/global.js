// نظام إدارة الجداول التشغيلية - JavaScript العام

document.addEventListener('DOMContentLoaded', function() {
    // تهيئة Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // تهيئة Popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // إخفاء الرسائل تلقائياً بعد 5 ثوان
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // تأكيد الحذف
    var deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            var message = this.getAttribute('data-confirm-message') || 'هل أنت متأكد من الحذف؟';
            if (confirm(message)) {
                this.closest('form').submit();
            }
        });
    });

    // تحديث حالة النماذج
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>جاري المعالجة...';
            }
        });
    });

    // البحث المباشر في الجداول
    var searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(function(input) {
        input.addEventListener('keyup', function() {
            var target = document.querySelector(this.getAttribute('data-search-target'));
            var filter = this.value.toLowerCase();
            var rows = target.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                var text = row.textContent.toLowerCase();
                if (text.indexOf(filter) > -1) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // تحديث العدادات
    updateCounters();
});

// دالة تحديث العدادات
function updateCounters() {
    // يمكن إضافة AJAX calls هنا لتحديث العدادات
    console.log('Updating counters...');
}

// دالة إظهار رسالة نجاح
function showSuccessMessage(message) {
    showAlert(message, 'success');
}

// دالة إظهار رسالة خطأ
function showErrorMessage(message) {
    showAlert(message, 'danger');
}

// دالة إظهار رسالة تحذير
function showWarningMessage(message) {
    showAlert(message, 'warning');
}

// دالة إظهار رسالة معلومات
function showInfoMessage(message) {
    showAlert(message, 'info');
}

// دالة إظهار التنبيهات
function showAlert(message, type) {
    var alertContainer = document.getElementById('alert-container') || createAlertContainer();
    var alertId = 'alert-' + Date.now();
    
    var alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // إخفاء التنبيه تلقائياً بعد 5 ثوان
    setTimeout(function() {
        var alert = document.getElementById(alertId);
        if (alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// إنشاء حاوية التنبيهات
function createAlertContainer() {
    var container = document.createElement('div');
    container.id = 'alert-container';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// دالة تحميل البيانات عبر AJAX
function loadData(url, callback) {
    fetch(url)
        .then(response => response.json())
        .then(data => callback(data))
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('حدث خطأ في تحميل البيانات');
        });
}

// دالة إرسال البيانات عبر AJAX
function sendData(url, data, callback) {
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => callback(data))
    .catch(error => {
        console.error('Error:', error);
        showErrorMessage('حدث خطأ في إرسال البيانات');
    });
}

// دالة الحصول على CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// دالة تنسيق التواريخ
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// دالة تنسيق الأوقات
function formatTime(timeString) {
    const time = new Date('1970-01-01T' + timeString);
    return time.toLocaleTimeString('ar-SA', {
        hour: '2-digit',
        minute: '2-digit'
    });
}
