import re

with open("script.js", "r", encoding="utf-8") as f:
    js = f.read()

global_helpers = """
// --- GLOBAL UI HELPERS ---
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    
    // Colors
    let iconColor = type === 'success' ? 'var(--success)' : 
                    type === 'warning' ? 'var(--warning)' : 
                    type === 'danger' ? 'var(--danger)' : 'var(--info)';
    let iconClass = type === 'success' ? 'fa-check-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 
                    type === 'danger' ? 'fa-times-circle' : 'fa-info-circle';
                    
    toast.innerHTML = `<i class="fas ${iconClass}" style="color: ${iconColor}; font-size: 1.25rem;"></i><span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Ensure pages get fade-in class
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab-pane').forEach(page => {
        page.classList.add('page-content');
    });
    
    // Add simple num-roll effect to big numbers
    document.querySelectorAll('.fs-2, .fs-1, h2, h1').forEach(el => {
        if(!isNaN(parseFloat(el.innerText)) && el.innerText.length < 10) {
            el.classList.add('num-roll');
        }
    });
});
"""

if "// --- GLOBAL UI HELPERS ---" not in js:
    with open("script.js", "a", encoding="utf-8") as f:
        f.write("\n\n" + global_helpers)
    print("Injected JS helpers.")
else:
    print("JS helpers already exist.")
