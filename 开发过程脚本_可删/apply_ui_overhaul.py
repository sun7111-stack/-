import re

with open("style.css", "r", encoding="utf-8") as f:
    css = f.read()

# Replace root variables and attach the comprehensive UI overhaul styles.
new_css = """/* UI OVERHAUL INJECTED */
:root {
    --primary-green: #10b981; 
    --primary-green-dark: #059669;
    --primary-green-light: #34d399;
    --primary-green-lightest: #d1fae5;

    --secondary-blue: #3b82f6;
    --border-color: #e5e7eb;
    --bg-light: #f3f4f6;
    --bg-white: #ffffff;
    
    --success: #10b981; /* Green */
    --warning: #f59e0b; /* Orange */
    --danger: #ef4444; /* Orange-red */
    --info: #3b82f6; /* Blue */
    --demo: #64748b; /* Gray-blue */

    --text-primary: #1f2937;
    --text-secondary: #4b5563;
    --text-muted: #9ca3af;

    --radius-md: 12px;
    --radius-lg: 16px;
    
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-hover: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    
    --transition-all: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-theme="dark"] {
    --bg-light: #111827;
    --bg-white: #1f2937;
    --border-color: #374151;
    --text-primary: #f9fafb;
    --text-secondary: #d1d5db;
    --text-muted: #9ca3af;
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    --shadow-hover: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

/* ================== CARDS ================== */
.card {
    border-radius: var(--radius-lg) !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: var(--shadow-md) !important;
    padding: 1.5rem !important; /* Unified padding */
    background-color: var(--bg-white) !important;
    transition: var(--transition-all) !important;
    color: var(--text-primary);
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover) !important;
}
.card-body { padding: 0 !important; }

/* ================== BUTTONS ================== */
.btn {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: var(--transition-all) !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}
.btn:hover {
    filter: brightness(1.1);
}
/* 主按钮：绿色实心 */
.btn-primary, .btn-success {
    background-color: var(--primary-green) !important;
    border-color: var(--primary-green) !important;
    color: #fff !important;
    box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3) !important;
}
/* 次按钮：白底描边 */
.btn-outline-primary, .btn-outline-secondary {
    background-color: transparent !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-secondary) !important;
}
.btn-outline-primary:hover, .btn-outline-secondary:hover {
    background-color: var(--bg-light) !important;
    color: var(--text-primary) !important;
}
/* 状态按钮/标签式 */
.btn-light, .badge {
    background-color: var(--bg-light) !important;
    color: var(--text-secondary) !important;
    border: none !important;
}

/* ================== TITLES & TEXT ================== */
h1, h2, h3, h4, h5, h6, .card-title {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.025em;
    margin-bottom: 0.75rem;
}
.text-muted, .small, p {
    color: var(--text-secondary) !important;
}
.badge.bg-success { background-color: var(--success) !important; color:#fff!important; }
.badge.bg-warning { background-color: var(--warning) !important; color:#fff!important; }
.badge.bg-danger { background-color: var(--danger) !important; color:#fff!important; }
.badge.bg-info { background-color: var(--info) !important; color:#fff!important; }

/* ================== LAYOUT: NAV & TOP BAR ================== */
/* Navbar / Top Bar */
.navbar {
    background-color: var(--bg-white) !important;
    border-bottom: 1px solid var(--border-color) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 0.75rem 1.5rem !important;
    height: 64px;
}
.navbar-brand { font-weight: 700; color: var(--text-primary) !important; }
/* Sidebar */
.sidebar {
    background-color: var(--bg-white) !important;
    border-right: 1px solid var(--border-color) !important;
}
.nav-link {
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    margin: 0.25rem 0.5rem;
    padding: 0.6rem 1rem !important;
    transition: var(--transition-all) !important;
}
.nav-link:hover {
    background-color: var(--bg-light) !important;
    color: var(--text-primary) !important;
    transform: translateX(4px);
}
.nav-link.active {
    background-color: var(--primary-green-lightest) !important;
    color: var(--primary-green-dark) !important;
    font-weight: 600;
}
[data-theme="dark"] .nav-link.active {
    background-color: rgba(16, 185, 129, 0.2) !important;
    color: var(--primary-green-light) !important;
}

/* Sidebar group titles */
.sidebar-heading {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-top: 1rem;
    padding: 0 1.5rem;
}

/* ================== ANIMATIONS & FEEDBACK ================== */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.page-content {   /* Apply to main views */
    animation: fadeIn 0.4s ease-out forwards;
}

/* Toast */
.toast-container {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    z-index: 9999;
}
.custom-toast {
    background: var(--bg-white);
    color: var(--text-primary);
    border-radius: 8px;
    box-shadow: var(--shadow-lg);
    padding: 1rem 1.5rem;
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border: 1px solid var(--border-color);
    animation: fadeIn 0.3s ease-out forwards;
}

/* Loading state for buttons */
.btn.loading {
    position: relative;
    pointer-events: none;
    opacity: 0.8;
}
.btn.loading::after {
    content: "";
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    margin-left: 0.5rem;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Numbers roll anim */
.num-roll {
    display: inline-block;
    animation: rollUp 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}
@keyframes rollUp {
    from { transform: translateY(50%); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
"""

with open("style.css", "a", encoding="utf-8") as f:
    f.write("\n\n" + new_css)

print("Applied CSS overhaul successfully.")
