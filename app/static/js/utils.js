/**
 * Shared utilities: fetch wrapper, toast notifications, helpers.
 */

// Fetch wrapper with error handling
async function api(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || 'Request failed');
        }
        return await response.json();
    } catch (err) {
        showToast(err.message, 'error');
        throw err;
    }
}

// Toast notification system
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = { info: '\u2139\ufe0f', success: '\u2705', warning: '\u26a0\ufe0f', error: '\u274c' };
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Format date for display
function formatDate(isoString) {
    if (!isoString) return '—';
    const d = new Date(isoString);
    return d.toLocaleDateString('de-DE', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

// Format relative time
function timeAgo(isoString) {
    if (!isoString) return 'Never';
    const now = new Date();
    const then = new Date(isoString);
    const seconds = Math.floor((now - then) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

// Status badge HTML
function statusBadge(status) {
    const colors = {
        online: 'bg-emerald-900 text-emerald-300',
        degraded: 'bg-yellow-900 text-yellow-300',
        offline: 'bg-red-900 text-red-300',
        unknown: 'bg-slate-700 text-slate-300',
        open: 'bg-blue-900 text-blue-300',
        in_progress: 'bg-yellow-900 text-yellow-300',
        resolved: 'bg-emerald-900 text-emerald-300',
        closed: 'bg-slate-700 text-slate-300',
    };
    const cls = colors[status] || 'bg-slate-700 text-slate-300';
    const label = status.replace('_', ' ');
    return `<span class="px-2 py-0.5 rounded-full text-xs font-medium ${cls}">${label}</span>`;
}

// Priority badge HTML
function priorityBadge(priority) {
    const cls = `priority-${priority}`;
    return `<span class="px-2 py-0.5 rounded-full text-xs font-medium ${cls}">${priority}</span>`;
}

// Close modal helper
function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
