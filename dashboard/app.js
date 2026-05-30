/**
 * Store Intelligence Dashboard — Client-side JavaScript
 *
 * Responsibilities:
 *   - Connect to WebSocket for real-time updates
 *   - Fetch metrics/funnel/heatmap/anomalies from API
 *   - Render Chart.js visualizations
 *   - Update KPI cards in real-time
 *
 * TODO: Implement:
 *   - WebSocket connection with reconnection logic
 *   - Chart.js initialization (funnel bar chart, heatmap)
 *   - Periodic API polling as WebSocket fallback
 *   - Anomaly alert rendering
 */

// ── Configuration ───────────────────────────────────────────

const CONFIG = {
    apiBase: window.location.origin,
    wsUrl: `ws://${window.location.host}/ws`,
    pollInterval: 10000, // 10 second fallback polling
};

// ── State ───────────────────────────────────────────────────

let ws = null;
let selectedStore = 'test_store';
let selectedWindow = '1h';
let funnelChart = null;
let heatmapChart = null;

// ── DOM References ──────────────────────────────────────────

const storeSelector = document.getElementById('store-selector');
const windowSelector = document.getElementById('window-selector');
const connectionStatus = document.getElementById('connection-status');

// KPI value elements
const kpiElements = {
    visitors: document.getElementById('kpi-visitors-value'),
    conversion: document.getElementById('kpi-conversion-value'),
    dwell: document.getElementById('kpi-dwell-value'),
    queue: document.getElementById('kpi-queue-value'),
    abandonment: document.getElementById('kpi-abandonment-value'),
};

// ── API Fetching ────────────────────────────────────────────

async function fetchMetrics() {
    // TODO: Implement API call to /stores/{id}/metrics
    // TODO: Update KPI cards with response data
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/metrics?window=${selectedWindow}`);
        const data = await res.json();
        updateKPICards(data);
    } catch (err) {
        console.error('Failed to fetch metrics:', err);
    }
}

async function fetchFunnel() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/funnel?window=${selectedWindow}`);
        if (!res.ok) throw new Error("Failed to fetch funnel");
        const data = await res.json();
        
        if (funnelChart && data.stages) {
            funnelChart.data.labels = data.stages.map(s => s.stage);
            funnelChart.data.datasets[0].data = data.stages.map(s => s.count);
            funnelChart.update();
        }
    } catch (err) {
        console.error('Failed to fetch funnel:', err);
    }
}

async function fetchHeatmap() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/heatmap`);
        if (!res.ok) throw new Error("Failed to fetch heatmap");
        const data = await res.json();
        
        if (heatmapChart && data.zones) {
            heatmapChart.data.labels = data.zones.map(z => z.zone_id);
            heatmapChart.data.datasets[0].data = data.zones.map(z => z.visit_count);
            heatmapChart.update();
        }
    } catch (err) {
        console.error('Failed to fetch heatmap:', err);
    }
}

async function fetchAnomalies() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/anomalies`);
        if (!res.ok) throw new Error("Failed to fetch anomalies");
        const data = await res.json();
        
        const listEl = document.getElementById('anomaly-list');
        if (!listEl) return;
        
        if (!data.anomalies || data.anomalies.length === 0) {
            listEl.innerHTML = '<p class="empty-state">No anomalies detected</p>';
            return;
        }
        
        listEl.innerHTML = data.anomalies.map(a => `
            <div class="anomaly-item ${a.severity.toLowerCase()}">
                <strong>${a.timestamp.substring(11,19)}</strong>: ${a.description}
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to fetch anomalies:', err);
    }
}

function initCharts() {
    const funnelCtx = document.getElementById('funnel-chart');
    if (funnelCtx) {
        funnelChart = new Chart(funnelCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Visitors',
                    data: [],
                    backgroundColor: '#9d4edd',
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    const heatmapCtx = document.getElementById('heatmap-chart');
    if (heatmapCtx) {
        heatmapChart = new Chart(heatmapCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Zone Visits',
                    data: [],
                    backgroundColor: '#ff9e00',
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' }
        });
    }
}

// ── UI Updates ──────────────────────────────────────────────

function updateKPICards(metrics) {
    // TODO: Add number formatting and animations
    if (kpiElements.visitors)    kpiElements.visitors.textContent = metrics.unique_visitors ?? '—';
    if (kpiElements.conversion)  kpiElements.conversion.textContent = metrics.conversion_rate != null ? `${(metrics.conversion_rate * 100).toFixed(1)}%` : '—';
    if (kpiElements.dwell)       kpiElements.dwell.textContent = metrics.avg_dwell_seconds != null ? `${Math.round(metrics.avg_dwell_seconds)}s` : '—';
    if (kpiElements.queue)       kpiElements.queue.textContent = metrics.queue_depth ?? '—';
    if (kpiElements.abandonment) kpiElements.abandonment.textContent = metrics.abandonment_rate != null ? `${(metrics.abandonment_rate * 100).toFixed(1)}%` : '—';
}

// ── WebSocket ───────────────────────────────────────────────

function connectWebSocket() {
    // Utilizing polling fallback for MVP
    if (connectionStatus) {
        connectionStatus.textContent = "Connected (Polling)";
        connectionStatus.style.background = "rgba(46, 213, 115, 0.2)";
        connectionStatus.style.color = "#2ed573";
    }

    // Polling
    setInterval(() => {
        fetchMetrics();
        fetchFunnel();
        fetchHeatmap();
        fetchAnomalies();
    }, CONFIG.pollInterval);
}

// ── Event Listeners ─────────────────────────────────────────

if (storeSelector) {
    storeSelector.addEventListener('change', (e) => {
        selectedStore = e.target.value;
        fetchMetrics();
    });
}

if (windowSelector) {
    windowSelector.addEventListener('change', (e) => {
        selectedWindow = e.target.value;
        fetchMetrics();
    });
}

// ── Initialize ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    console.log('Store Intelligence Dashboard initialized');
    initCharts();
    
    // Initial fetch
    fetchMetrics();
    fetchFunnel();
    fetchHeatmap();
    fetchAnomalies();
    
    connectWebSocket();
});
