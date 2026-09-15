function showToast(message, type = 'success', duration = 3500) {
    let container = document.querySelector('.sg-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'sg-toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `sg-toast ${type}`;

    let icon = '✓';
    if (type === 'error') icon = '✕';
    if (type === 'info') icon = 'ℹ';

    toast.innerHTML = `
        <span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:rgba(255,255,255,0.15); font-size:0.8rem; font-weight:900;">${icon}</span>
        <span style="flex:1; line-height:1.3;">${message}</span>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

window.mostrarToast = showToast;
