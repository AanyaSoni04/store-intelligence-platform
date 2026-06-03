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

const BACKEND_URL = 'https://store-intelligence-api-76n7.onrender.com'; // 🛑 REPLACE THIS WITH YOUR ACTUAL RENDER URL

const CONFIG = {
    apiBase: BACKEND_URL,
    wsUrl: `${BACKEND_URL.replace('http', 'ws')}/ws`,
    pollInterval: 10000, // 10 second fallback polling
};

// ── State ───────────────────────────────────────────────────

let ws = null;
let selectedStore = 'my_store';
let selectedWindow = '7d'; // Default to 7d to ensure real data is shown on load
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
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/metrics?window=${selectedWindow}`);
        if (!res.ok) throw new Error("Failed to fetch metrics");
        const data = await res.json();
        console.log("Metrics API Response:", data);
        updateKPICards(data);
        updateLastRefreshTime();
    } catch (err) {
        console.error('Failed to fetch metrics:', err);
    }
}

async function fetchFunnel() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/funnel?window=${selectedWindow}`);
        if (!res.ok) throw new Error("Failed to fetch funnel");
        const data = await res.json();
        console.log("Funnel API Response:", data);

        if (funnelChart && data.stages) {
            // Support both 'value' and 'count' just in case of mismatch
            funnelChart.data.labels = data.stages.map(s => s.stage.replace('_', ' '));
            funnelChart.data.datasets[0].data = data.stages.map(s => s.count !== undefined ? s.count : s.value);
            funnelChart.update();

            // Render drop-offs
            const dropoffsContainer = document.getElementById('funnel-dropoffs');
            if (dropoffsContainer && data.drop_off_rates) {
                const keys = Object.keys(data.drop_off_rates);
                dropoffsContainer.innerHTML = keys.map(key => {
                    const rate = data.drop_off_rates[key];
                    if (rate === 0) return ''; // Skip 0% drop-offs for cleaner UI
                    const formattedName = key.split('_to_').map(k => k.replace('_', ' ')).join(' → ');
                    return `<div class="dropoff-item">
                        <strong>${(rate * 100).toFixed(1)}% drop</strong>
                        <span>${formattedName}</span>
                    </div>`;
                }).join('');
            }
        }
    } catch (err) {
        console.error('Failed to fetch funnel:', err);
    }
}

async function fetchHeatmap() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/heatmap?window=${selectedWindow}`);
        if (!res.ok) throw new Error("Failed to fetch heatmap");
        const data = await res.json();
        console.log("Heatmap API Response:", data);

        if (heatmapChart && data.zones) {
            // Rank zones by volume
            const sortedZones = [...data.zones].sort((a, b) => b.visit_count - a.visit_count);

            heatmapChart.data.labels = sortedZones.map(z => z.zone_id.replace('_', ' ').toUpperCase());
            heatmapChart.data.datasets[0].data = sortedZones.map(z => z.visit_count);
            heatmapChart.update();
        }
    } catch (err) {
        console.error('Failed to fetch heatmap:', err);
    }
}

async function fetchAnomalies() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/stores/${selectedStore}/anomalies?window=${selectedWindow}`);
        if (!res.ok) throw new Error("Failed to fetch anomalies");
        const data = await res.json();
        console.log("Anomalies API Response:", data);

        const listEl = document.getElementById('anomaly-list');
        if (!listEl) return;

        if (!data.anomalies || data.anomalies.length === 0) {
            listEl.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">✓</div>
                    <p>System operating normally. No anomalies detected.</p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = data.anomalies.map(a => `
            <div class="anomaly-item ${a.severity.toLowerCase()}">
                <span class="severity-badge">${a.severity}</span>
                <span class="anomaly-desc">${a.description}</span>
                <span class="anomaly-time">${new Date(a.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to fetch anomalies:', err);
    }
}

// Custom plugin to draw values on bars
const valueLabelPlugin = {
    id: 'valueLabels',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        chart.data.datasets.forEach((dataset, i) => {
            const meta = chart.getDatasetMeta(i);
            meta.data.forEach((bar, index) => {
                const data = dataset.data[index];
                if (data > 0) {
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                    ctx.textAlign = chart.config.options.indexAxis === 'y' ? 'left' : 'center';
                    ctx.textBaseline = chart.config.options.indexAxis === 'y' ? 'middle' : 'bottom';
                    ctx.font = 'bold 14px Inter, sans-serif';

                    const x = chart.config.options.indexAxis === 'y' ? bar.x + 8 : bar.x;
                    const y = chart.config.options.indexAxis === 'y' ? bar.y : bar.y - 8;
                    ctx.fillText(data, x, y);
                }
            });
        });
    }
};

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
                    backgroundColor: 'rgba(123, 44, 191, 0.8)', // #7B2CBF
                    borderColor: '#7B2CBF',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            plugins: [valueLabelPlugin],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: 'rgba(0, 0, 0, 0.03)' }, border: { display: false }, ticks: { font: { family: 'Inter', size: 14 }, color: '#718096' } },
                    x: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 14, weight: 600 }, color: '#4A5568' } }
                },
                plugins: { legend: { display: false } }
            }
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
                    backgroundColor: 'rgba(199, 125, 255, 0.8)', // #C77DFF
                    borderColor: '#C77DFF',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            plugins: [valueLabelPlugin],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: { grid: { color: 'rgba(0, 0, 0, 0.03)' }, border: { display: false }, ticks: { font: { family: 'Inter', size: 14 }, color: '#718096' } },
                    y: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 14, weight: 600 }, color: '#4A5568' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}

// ── UI Updates ──────────────────────────────────────────────

function updateKPICards(metrics) {
    // Support nested data in case it's wrapped
    const data = metrics.metrics ? metrics.metrics : metrics;

    // Support both 'unique_visitors' and 'visitors'
    const visitors = data.unique_visitors !== undefined ? data.unique_visitors : data.visitors;

    // Add number formatting and animations
    if (kpiElements.visitors) kpiElements.visitors.textContent = visitors ?? '—';
    if (kpiElements.conversion) kpiElements.conversion.textContent = data.conversion_rate != null ? `${(data.conversion_rate * 100).toFixed(1)}%` : '—';
    if (kpiElements.dwell) kpiElements.dwell.textContent = data.avg_dwell_seconds != null ? `${Math.round(data.avg_dwell_seconds)}s` : '—';
    if (kpiElements.queue) kpiElements.queue.textContent = data.queue_depth ?? '—';
    if (kpiElements.abandonment) kpiElements.abandonment.textContent = data.abandonment_rate != null ? `${(data.abandonment_rate * 100).toFixed(1)}%` : '—';
}

function updateLastRefreshTime() {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const el1 = document.getElementById('last-refresh-time');
    const el2 = document.getElementById('mon-cam-refresh-bottom');
    if (el1) el1.textContent = timeStr;
    if (el2) el2.textContent = timeStr;
}

// ── WebSocket ───────────────────────────────────────────────

function connectWebSocket() {
    const ws = new WebSocket(CONFIG.wsUrl);

    ws.onopen = () => {
        const connectionStatus = document.getElementById('connection-status');
        const landingWsStatus = document.getElementById('landing-ws-status');
        const topWsStatus = document.getElementById('top-ws-status');
        const camWsStatus = document.getElementById('cam-ws-status');
        const hBadgeWs = document.getElementById('h-badge-ws');

        if (connectionStatus) {
            connectionStatus.textContent = "Connected";
            connectionStatus.className = "status-badge connected";
        }
        if (landingWsStatus) {
            landingWsStatus.textContent = "Connected";
            landingWsStatus.style.color = "var(--success)";
        }
        if (topWsStatus) {
            topWsStatus.className = "live-badge connected";
        }
        if (camWsStatus) {
            camWsStatus.className = "live-badge connected";
            camWsStatus.innerHTML = '<span class="pulse-dot"></span> Connected';
        }
        if (hBadgeWs) {
            hBadgeWs.className = "h-badge success";
            hBadgeWs.innerHTML = '<i data-lucide="check-circle"></i> WebSocket Connected';
            lucide.createIcons();
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // Instant Reactivity: Refresh data exactly when new pipeline events land
        if (data.type === "EVENTS_INGESTED") {
            fetchMetrics();
            fetchFunnel();
            fetchHeatmap();
            fetchAnomalies();
            fetchHealthStats();
        } else if (data.type === 'LIVE_TELEMETRY') {
            const tel = data.data;
            const activeCam = document.getElementById('cam-info-id');
            // Only update if viewing the relevant camera
            if (activeCam && activeCam.textContent === tel.camera_id) {
                const visitorsEl = document.getElementById('live-active-visitors');
                const tracksEl = document.getElementById('live-active-tracks');
                const zoneListEl = document.getElementById('live-zone-occupancy');
                const eventEl = document.getElementById('live-last-event');
                const dot = document.getElementById('live-indicator-dot');

                if (visitorsEl) visitorsEl.textContent = tel.active_visitors;
                if (tracksEl) tracksEl.textContent = tel.active_tracks;

                if (zoneListEl) {
                    const zones = Object.entries(tel.zone_occupancy);
                    if (zones.length > 0) {
                        zoneListEl.innerHTML = zones.map(([z, count]) => `
                            <div class="live-zone-row">
                                <strong>${z}</strong>
                                <span>${count}</span>
                            </div>
                        `).join('');
                    } else {
                        zoneListEl.innerHTML = `<span style="font-size: 13px; color: var(--text-muted); font-style: italic;">No active zones</span>`;
                    }
                }

                if (eventEl) {
                    const ts = new Date(tel.timestamp);
                    eventEl.textContent = ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }

                // Flash the live indicator
                if (dot) {
                    dot.classList.remove('active');
                    void dot.offsetWidth; // trigger reflow
                    dot.classList.add('active');
                }
            }
        }
    };

    ws.onclose = () => {
        const connectionStatus = document.getElementById('connection-status');
        const landingWsStatus = document.getElementById('landing-ws-status');
        const topWsStatus = document.getElementById('top-ws-status');
        const camWsStatus = document.getElementById('cam-ws-status');
        const hBadgeWs = document.getElementById('h-badge-ws');

        if (connectionStatus) {
            connectionStatus.textContent = "Disconnected (Retrying...)";
            connectionStatus.style.background = "rgba(239, 68, 68, 0.2)";
            connectionStatus.style.color = "var(--danger)";
        }
        if (landingWsStatus) {
            landingWsStatus.textContent = "Disconnected";
            landingWsStatus.style.color = "var(--danger)";
        }
        if (topWsStatus) {
            topWsStatus.className = "live-badge";
        }
        if (camWsStatus) {
            camWsStatus.className = "live-badge";
            camWsStatus.innerHTML = '<span class="pulse-dot"></span> Disconnected';
        }
        if (hBadgeWs) {
            hBadgeWs.className = "h-badge";
            hBadgeWs.innerHTML = '<i data-lucide="loader"></i> WebSocket Disconnected';
            lucide.createIcons();
        }
        // Auto-reconnect loop if the API container restarts
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.error("WebSocket encountered an error: ", err);
        ws.close();
    };
}

async function fetchHealthStats() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/health`);
        if (res.ok) {
            const data = await res.json();
            const totalEventsEl = document.getElementById('landing-total-events');
            if (totalEventsEl && data.event_count !== undefined) {
                totalEventsEl.textContent = data.event_count.toLocaleString();
            }
        }
    } catch (e) {
        console.error("Failed to fetch health stats", e);
    }
}

// ── Camera Intelligence ─────────────────────────────────────

async function initCameraController() {
    const tabs = document.querySelectorAll('.cam-tab');
    if (tabs.length === 0) return;

    const cameras = [
        { id: 'CAM 1', file: 'cam1.mp4', config: 'cam_001.json' },
        { id: 'CAM 2', file: 'cam2.mp4', config: 'cam_002.json' },
        { id: 'CAM 3', file: 'cam3.mp4', config: 'cam_003.json' },
        { id: 'CAM 4', file: 'cam4.mp4', config: 'cam_004.json' },
        { id: 'CAM 5', file: 'cam5.mp4', config: 'cam_005.json' }
    ];

    async function selectCamera(index) {
        // Update tabs
        tabs.forEach(t => t.classList.remove('active'));
        tabs[index].classList.add('active');

        const cam = cameras[index];

        // Update video
        const videoPlayer = document.getElementById('cam-video-player');
        if (videoPlayer) {
            videoPlayer.src = `assets/videos/${cam.file}`;
            videoPlayer.play().catch(e => console.log('Autoplay prevented:', e));
        }

        // Update metadata
        const idEl = document.getElementById('cam-info-id');
        const fileEl = document.getElementById('cam-info-file');
        const monCamIdBottom = document.getElementById('mon-cam-id-bottom');

        if (idEl) idEl.textContent = cam.id;
        if (fileEl) fileEl.textContent = cam.file;
        if (monCamIdBottom) monCamIdBottom.textContent = cam.id;

        // Fetch and display zones
        const zonesContainer = document.getElementById('cam-active-zones');
        const zonesCountBottom = document.getElementById('mon-cam-zones-bottom');
        const zoneConfigPanel = document.getElementById('zone-config-panel');
        const impactTags = document.getElementById('cam-impact-tags');

        if (zonesContainer) zonesContainer.innerHTML = `<span class="zone-badge" style="background:#cbd5e0; color:#4a5568;">Loading...</span>`;
        if (zoneConfigPanel) zoneConfigPanel.innerHTML = '';
        if (impactTags) impactTags.innerHTML = '';

        try {
            const res = await fetch(`assets/zones/${cam.config}`);
            if (res.ok) {
                const data = await res.json();
                let zones = [];
                if (data.zones && Array.isArray(data.zones)) zones = data.zones;
                else if (Array.isArray(data)) zones = data;

                if (zonesCountBottom) zonesCountBottom.textContent = zones.length;

                let impactSet = new Set(['<span class="impact-tag"><i data-lucide="check"></i> Anomaly Detection</span>']);

                if (zones.length > 0) {
                    if (zonesContainer) {
                        zonesContainer.innerHTML = zones.map(z => `<span class="zone-badge">${z.zone_id || z.name || 'Unknown'}</span>`).join('');
                    }
                    if (zoneConfigPanel) {
                        zoneConfigPanel.innerHTML = zones.map(z => {
                            const name = z.zone_id || z.name || 'Unknown';
                            const purpose = (name.includes('browsing') ? 'Product Browsing Analytics' :
                                (name.includes('entrance') ? 'Footfall Measurement' :
                                    (name.includes('billing') || name.includes('checkout') ? 'Queue & Conversion Analytics' :
                                        (name.includes('stock') ? 'Staff / Inventory Area' : 'Spatial Tracking'))));

                            if (purpose.includes('Queue')) impactSet.add('<span class="impact-tag"><i data-lucide="check"></i> Queue Monitoring</span>');
                            if (purpose.includes('Conversion')) impactSet.add('<span class="impact-tag"><i data-lucide="check"></i> Conversion Tracking</span>');
                            if (purpose.includes('Footfall') || purpose.includes('Browsing')) impactSet.add('<span class="impact-tag"><i data-lucide="check"></i> Funnel Analytics</span>');
                            impactSet.add('<span class="impact-tag"><i data-lucide="check"></i> Heatmap Analytics</span>');

                            return `<div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-main); padding:10px 16px; border-radius:6px; border:1px solid var(--border-color);">
                                <div><strong style="font-size:13px; color:var(--text-main); display:block;">${name}</strong><span style="font-size:11px; color:var(--text-muted); font-style:italic;">${purpose}</span></div>
                                <span class="zone-badge">Active</span>
                            </div>`;
                        }).join('');
                    }
                } else {
                    if (zonesContainer) zonesContainer.innerHTML = `<span class="zone-badge" style="background:#e2e8f0; color:#64748b;">No zones defined</span>`;
                }

                if (impactTags) impactTags.innerHTML = Array.from(impactSet).join('');
                lucide.createIcons();
            } else {
                if (zonesContainer) zonesContainer.innerHTML = `<span class="zone-badge" style="background:#fee2e2; color:#ef4444;">Failed to load config</span>`;
            }
        } catch (err) {
            console.error('Error fetching zones:', err);
            if (zonesContainer) zonesContainer.innerHTML = `<span class="zone-badge" style="background:#fee2e2; color:#ef4444;">Error loading config</span>`;
        }
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            const index = parseInt(e.currentTarget.getAttribute('data-index'), 10);
            selectCamera(index);
        });
    });

    // Initialize first camera
    selectCamera(0);
}

async function fetchTotalActiveZones() {
    const cameras = ['cam_001.json', 'cam_002.json', 'cam_003.json', 'cam_004.json', 'cam_005.json'];
    let total = 0;

    for (const config of cameras) {
        try {
            const res = await fetch(`assets/zones/${config}`);
            if (res.ok) {
                const data = await res.json();
                if (data.zones && Array.isArray(data.zones)) {
                    total += data.zones.length;
                } else if (Array.isArray(data)) {
                    total += data.length;
                }
            }
        } catch (e) {
            console.error(`Failed to load ${config} for tally`, e);
        }
    }

    const activeZonesEl = document.getElementById('landing-active-zones');
    if (activeZonesEl) {
        activeZonesEl.textContent = total;
    }
}

async function renderCoverageSummary() {
    const cameras = [
        { id: 'CAM 1', config: 'cam_001.json' },
        { id: 'CAM 2', config: 'cam_002.json' },
        { id: 'CAM 3', config: 'cam_003.json' },
        { id: 'CAM 4', config: 'cam_004.json' },
        { id: 'CAM 5', config: 'cam_005.json' }
    ];
    const grid = document.getElementById('full-coverage-grid');
    if (!grid) return;

    let html = '';
    for (const cam of cameras) {
        try {
            const res = await fetch(`assets/zones/${cam.config}`);
            if (res.ok) {
                const data = await res.json();
                let zones = [];
                if (data.zones && Array.isArray(data.zones)) zones = data.zones;
                else if (Array.isArray(data)) zones = data;

                if (zones.length === 0) continue;

                const zoneNames = zones.map(z => z.zone_id || z.name || 'Unknown');
                const hasQueue = zoneNames.some(z => z.includes('billing') || z.includes('checkout'));
                const hasEntrance = zoneNames.some(z => z.includes('entrance'));
                const hasBrowsing = zoneNames.some(z => z.includes('browsing'));

                let purpose = 'Spatial Tracking';
                let analytics = 'Heatmap Analytics';
                let events = 'Zone Enter, Zone Exit';

                if (hasQueue) {
                    purpose = 'Queue Monitoring & Purchase Proxy';
                    analytics = 'Conversion Analytics, Queue Analytics';
                    events = 'Queue Join, Queue Exit, Purchase Proxy';
                } else if (hasEntrance) {
                    purpose = 'Store Entry Measurement';
                    analytics = 'Footfall Analytics';
                    events = 'Entry Detection, Exit Detection';
                } else if (hasBrowsing) {
                    purpose = 'Product Browsing Observation';
                    analytics = 'Funnel Analytics, Heatmap Analytics';
                    events = 'Zone Enter, Zone Exit';
                }

                const renderBadges = (str, bg, col) => {
                    return str.split(', ').map(s => `<span style="background: ${bg}; color: ${col}; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; display: inline-block; margin-right: 4px; margin-bottom: 4px;">${s}</span>`).join('');
                };

                html += `
                <div class="coverage-card" style="display: flex; flex-direction: column; gap: 12px; padding: 16px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: var(--shadow-sm);">
                    <div style="display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px;">
                        <i data-lucide="video" style="width: 18px; height: 18px; color: var(--primary);"></i>
                        <strong style="font-size: 16px; color: var(--text-main);">${cam.id}</strong>
                    </div>
                    
                    <div style="font-size: 13px; color: var(--text-main); display: flex; flex-direction: column; gap: 4px;">
                        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Covered Zone(s)</span>
                        <div style="font-family: var(--font-mono); font-size: 12px; font-weight: 500;">${zoneNames.join(', ')}</div>
                    </div>
                    
                    <div style="font-size: 13px; color: var(--text-main); display: flex; flex-direction: column; gap: 4px;">
                        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Business Purpose</span>
                        <div style="font-weight: 500;">${purpose}</div>
                    </div>

                    <div style="font-size: 13px; color: var(--text-main); display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
                        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Analytics Generated</span>
                        <div>${renderBadges(analytics, '#e2e8f0', '#4a5568')}</div>
                    </div>

                    <div style="font-size: 13px; color: var(--text-main); display: flex; flex-direction: column; gap: 4px;">
                        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Events Produced</span>
                        <div>${renderBadges(events, '#e6fffa', '#234e52')}</div>
                    </div>
                </div>`;
            }
        } catch (e) {
            console.error(`Failed to load coverage for ${cam.config}`, e);
        }
    }
    grid.innerHTML = html;
    lucide.createIcons();
}

// ── Event Listeners ─────────────────────────────────────────

if (storeSelector) {
    storeSelector.addEventListener('change', (e) => {
        selectedStore = e.target.value;
        fetchMetrics();
        fetchFunnel();
        fetchHeatmap();
        fetchAnomalies();
    });
}

if (windowSelector) {
    windowSelector.addEventListener('change', (e) => {
        selectedWindow = e.target.value;
        fetchMetrics();
        fetchFunnel();
        fetchHeatmap();
        fetchAnomalies();
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
    fetchHealthStats();
    initCameraController();
    fetchTotalActiveZones();
    renderCoverageSummary();

    // Initialize Navigation Routing
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const targetId = e.currentTarget.getAttribute('data-target');
            if (targetId) {
                e.preventDefault();
                // Remove active classes
                navLinks.forEach(l => l.classList.remove('active'));
                pages.forEach(p => p.classList.remove('active'));

                // Set active class
                e.currentTarget.classList.add('active');
                const targetPage = document.getElementById(targetId);
                if (targetPage) {
                    targetPage.classList.add('active');
                }
            }
        });
    });

    connectWebSocket();
});
