// 主要JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// 通用AJAX请求函数
function makeRequest(url, method = 'POST', data = {}) {
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: method !== 'GET' ? JSON.stringify(data) : null
    }).then(response => response.json());
}

// 显示加载状态
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

// 隐藏加载状态
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// 显示消息
function showMessage(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 找到容器并插入消息
    const container = document.querySelector('.container');
    const existingAlerts = container.querySelector('.alert');
    if (existingAlerts) {
        existingAlerts.remove();
    }
    
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // 自动隐藏成功消息
    if (type === 'success') {
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }
}