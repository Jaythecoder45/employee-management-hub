document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});

// Copy to Clipboard Utility
function copyToClipboard(text, message) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(message);
        }).catch(err => {
            console.error('Failed to copy: ', err);
            fallbackCopy(text, message);
        });
    } else {
        fallbackCopy(text, message);
    }
}

function fallbackCopy(text, message) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast(message);
        }
    } catch (err) {
        console.error('Fallback copy failed: ', err);
    }
    document.body.removeChild(textArea);
}

function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    toast.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 2700);
}
