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
let selectedStore = 'store_001';
let selectedWindow = '1h';

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
    // TODO: Implement API call to /stores/{id}/funnel
    // TODO: Update funnel Chart.js chart
    console.log('TODO: Fetch and render funnel');
}

async function fetchHeatmap() {
    // TODO: Implement API call to /stores/{id}/heatmap
    // TODO: Update heatmap Chart.js chart
    console.log('TODO: Fetch and render heatmap');
}

async function fetchAnomalies() {
    // TODO: Implement API call to /stores/{id}/anomalies
    // TODO: Render anomaly alert cards
    console.log('TODO: Fetch and render anomalies');
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
    // TODO: Implement WebSocket connection with auto-reconnect
    // TODO: Handle incoming event/metric updates
    // TODO: Update connection status badge
    console.log('TODO: WebSocket connection not yet implemented');

    // Fallback to polling
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
    fetchMetrics();
    connectWebSocket();
});
