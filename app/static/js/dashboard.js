/**
 * Dashboard page: KPI cards, charts, live feed, recent tickets.
 */

let statusChart = null;
let responseChart = null;

// Load dashboard data
async function loadDashboard() {
    try {
        const [stats, ticketStats, services, logs] = await Promise.all([
            api('/api/services/stats'),
            api('/api/tickets/stats'),
            api('/api/services'),
            api('/api/logs?limit=20'),
        ]);

        // Update KPI cards
        document.getElementById('kpi-total').textContent = stats.total;
        document.getElementById('kpi-online').textContent = stats.online;
        document.getElementById('kpi-online-pct').textContent = `(${stats.online_percentage}%)`;
        document.getElementById('kpi-tickets').textContent = ticketStats.open + ticketStats.in_progress;
        document.getElementById('kpi-response').textContent = stats.avg_response_time_ms || '—';

        // Status donut chart
        renderStatusChart(stats);

        // Response time bar chart
        renderResponseChart(services);

        // Live feed from logs
        renderLiveFeed(logs);

        // Recent tickets
        loadRecentTickets();
    } catch (err) {
        console.error('Dashboard load error:', err);
    }
}

function renderStatusChart(stats) {
    const ctx = document.getElementById('status-chart').getContext('2d');
    if (statusChart) statusChart.destroy();

    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Online', 'Degraded', 'Offline', 'Unknown'],
            datasets: [{
                data: [stats.online, stats.degraded, stats.offline, stats.unknown],
                backgroundColor: ['#34d399', '#fbbf24', '#f87171', '#64748b'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', font: { size: 12 } }
                }
            },
            cutout: '65%',
        }
    });
}

function renderResponseChart(services) {
    const ctx = document.getElementById('response-chart').getContext('2d');
    if (responseChart) responseChart.destroy();

    const sorted = services
        .filter(s => s.response_time_ms != null)
        .sort((a, b) => b.response_time_ms - a.response_time_ms)
        .slice(0, 8);

    responseChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(s => s.name),
            datasets: [{
                label: 'Response Time (ms)',
                data: sorted.map(s => s.response_time_ms),
                backgroundColor: sorted.map(s =>
                    s.response_time_ms < 200 ? '#34d399' :
                    s.response_time_ms < 1000 ? '#fbbf24' : '#f87171'
                ),
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#1e293b' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { size: 11 } }
                }
            }
        }
    });
}

function renderLiveFeed(logs) {
    const feed = document.getElementById('live-feed');
    if (logs.length === 0) {
        feed.innerHTML = '<div class="text-sm text-slate-500 text-center py-8">No events yet</div>';
        return;
    }

    feed.innerHTML = logs.map(log => {
        const colors = {
            INFO: 'text-blue-400', WARNING: 'text-yellow-400',
            ERROR: 'text-red-400', CRITICAL: 'text-red-500 font-bold',
        };
        const cls = colors[log.level] || 'text-slate-400';
        return `
            <div class="flex items-start gap-2 text-sm py-1 border-b border-slate-700/50">
                <span class="text-slate-500 whitespace-nowrap text-xs mt-0.5">${timeAgo(log.timestamp)}</span>
                <span class="${cls} whitespace-nowrap text-xs">[${log.level}]</span>
                <span class="text-slate-300">${escapeHtml(log.message)}</span>
            </div>
        `;
    }).join('');
}

async function loadRecentTickets() {
    try {
        const tickets = await api('/api/tickets?sort_by=created_at&order=desc');
        const recent = tickets.slice(0, 5);
        const container = document.getElementById('recent-tickets');

        if (recent.length === 0) {
            container.innerHTML = '<div class="text-sm text-slate-500 text-center py-8">No tickets</div>';
            return;
        }

        container.innerHTML = recent.map(t => `
            <div class="flex items-center justify-between py-2 border-b border-slate-700/50">
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium truncate">${escapeHtml(t.title)}</div>
                    <div class="text-xs text-slate-500">${timeAgo(t.created_at)} · ${t.category || 'General'}</div>
                </div>
                <div class="flex items-center gap-2 ml-2">
                    ${priorityBadge(t.priority)}
                    ${statusBadge(t.status)}
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Load tickets error:', err);
    }
}

// Handle WebSocket events on dashboard
window.addEventListener('ws-event', (e) => {
    const event = e.detail;
    const feed = document.getElementById('live-feed');

    // Add event to live feed
    const colors = {
        service_status_change: event.data?.new_status === 'offline' ? 'text-red-400' : 'text-yellow-400',
        ticket_created: 'text-blue-400',
        critical_log: 'text-red-500 font-bold',
    };

    let message = '';
    if (event.type === 'service_status_change') {
        message = `Service '${event.data.service_name}' changed: ${event.data.old_status} → ${event.data.new_status}`;
    } else if (event.type === 'ticket_created') {
        message = `New ticket: ${event.data.title} (${event.data.priority})`;
    }

    if (message) {
        const div = document.createElement('div');
        div.className = 'flex items-start gap-2 text-sm py-1 border-b border-slate-700/50';
        div.innerHTML = `
            <span class="text-slate-500 whitespace-nowrap text-xs mt-0.5">Just now</span>
            <span class="${colors[event.type] || 'text-slate-400'} whitespace-nowrap text-xs">[EVENT]</span>
            <span class="text-slate-300">${escapeHtml(message)}</span>
        `;

        // Remove placeholder if exists
        const placeholder = feed.querySelector('.text-center');
        if (placeholder) feed.innerHTML = '';

        feed.insertBefore(div, feed.firstChild);

        // Keep max 50 entries
        while (feed.children.length > 50) {
            feed.removeChild(feed.lastChild);
        }
    }

    // Refresh data after events
    loadDashboard();
});

// Initial load + auto refresh every 30s
loadDashboard();
setInterval(loadDashboard, 30000);
