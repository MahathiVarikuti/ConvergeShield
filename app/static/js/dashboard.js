// ConvergeShield Dashboard JavaScript
// Real-time monitoring and anomaly visualization

let streamInterval = null;
let normalCount = 0;
let anomalyCount = 0;
let blockedCount = 0;
let correctPredictions = 0;
let totalPredictions = 0;

// Chart instances
let modelScoresChart = null;
let timelineChart = null;

// Timeline data (limited to 30 points)
const MAX_TIMELINE_POINTS = 30;
const MAX_TABLE_ROWS = 20;

const timelineData = {
    labels: [],
    normal: [],
    anomaly: []
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    checkSystemStatus();
});

function initCharts() {
    // Model Scores Chart
    const modelCtx = document.getElementById('modelScoresChart');
    if (!modelCtx) return;
    
    modelScoresChart = new Chart(modelCtx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Isolation Forest', 'Random Forest', 'XGBoost', 'Ensemble'],
            datasets: [{
                label: 'Anomaly Score',
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(245, 158, 11, 0.7)',
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(139, 92, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)'
                ],
                borderColor: [
                    '#f59e0b',
                    '#3b82f6',
                    '#8b5cf6',
                    '#10b981'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    grid: { color: '#2d3a4f' },
                    ticks: { color: '#9ca3af' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart');
    if (!timelineCtx) return;
    
    timelineChart = new Chart(timelineCtx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Normal',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Anomaly',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#2d3a4f' },
                    ticks: { color: '#9ca3af' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af', maxTicksLimit: 10 }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e5e7eb' }
                }
            }
        }
    });
}

async function checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'ready') {
            document.getElementById('systemStatus').innerHTML = 
                '<i class="fas fa-circle me-1"></i>ONLINE';
            document.getElementById('systemStatus').className = 'badge bg-success me-3';
        } else {
            document.getElementById('systemStatus').innerHTML = 
                '<i class="fas fa-circle me-1"></i>OFFLINE';
            document.getElementById('systemStatus').className = 'badge bg-danger me-3';
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

function startStream() {
    const speed = parseInt(document.getElementById('speedSelect').value);
    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;
    document.getElementById('detectionDetails').style.display = 'block';
    
    streamInterval = setInterval(fetchStreamData, speed);
    fetchStreamData(); // Immediate first fetch
}

function stopStream() {
    if (streamInterval) {
        clearInterval(streamInterval);
        streamInterval = null;
    }
    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
}

async function fetchStreamData() {
    try {
        const response = await fetch('/api/stream');
        const data = await response.json();
        
        if (data.error) {
            console.error('Stream error:', data.error);
            return;
        }
        
        updateDisplay(data);
        updateStats(data);
        updateCharts(data);
        updateTable(data);
        updateSHAP(data);
        updateIPS(data);
        updateSCADAStatus(data);
        
    } catch (error) {
        console.error('Stream fetch failed:', error);
    }
}

function updateDisplay(data) {
    const statusDiv = document.getElementById('detectionStatus');
    
    if (data.prediction === 1) {
        statusDiv.className = 'detection-status anomaly';
        statusDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>ANOMALY DETECTED</span>
        `;
    } else {
        statusDiv.className = 'detection-status normal';
        statusDiv.innerHTML = `
            <i class="fas fa-shield-alt"></i>
            <span>NORMAL</span>
        `;
    }
    
    // Update confidence bar
    const confidence = (data.confidence * 100).toFixed(1);
    const confidenceBar = document.getElementById('confidenceBar');
    confidenceBar.style.width = confidence + '%';
    confidenceBar.className = data.prediction === 1 ? 'progress-bar anomaly' : 'progress-bar';
    document.getElementById('confidenceValue').textContent = confidence + '%';
    
    // Physics status
    const physicsDiv = document.getElementById('physicsStatus');
    if (data.physics_valid) {
        physicsDiv.innerHTML = '<span class="badge bg-success">VALID</span>';
    } else {
        physicsDiv.innerHTML = `<span class="badge bg-warning">${data.physics_violations} violations</span>`;
    }
    
    // IPS action
    const ipsDiv = document.getElementById('ipsAction');
    if (data.ips_action === 'BLOCK') {
        ipsDiv.innerHTML = '<span class="badge bg-danger">BLOCKED</span>';
    } else if (data.ips_action === 'ALERT') {
        ipsDiv.innerHTML = '<span class="badge bg-warning">ALERT</span>';
    } else {
        ipsDiv.innerHTML = '<span class="badge bg-secondary">-</span>';
    }
}

function updateStats(data) {
    totalPredictions++;
    
    if (data.prediction === 0) {
        normalCount++;
    } else {
        anomalyCount++;
        if (data.ips_severity === 'critical') {
            blockedCount++;
        }
    }
    
    if (data.correct) {
        correctPredictions++;
    }
    
    document.getElementById('normalCount').textContent = normalCount;
    document.getElementById('anomalyCount').textContent = anomalyCount;
    document.getElementById('blockedCount').textContent = blockedCount;
    
    const accuracy = ((correctPredictions / totalPredictions) * 100).toFixed(1);
    document.getElementById('accuracyRate').textContent = accuracy + '%';
}

function updateCharts(data) {
    if (!modelScoresChart || !timelineChart) return;
    
    // Update model scores chart
    modelScoresChart.data.datasets[0].data = [
        data.individual_scores.isolation_forest,
        data.individual_scores.random_forest,
        data.individual_scores.xgboost,
        data.confidence
    ];
    modelScoresChart.update('none');
    
    // Update timeline
    const now = new Date().toLocaleTimeString();
    timelineData.labels.push(now);
    timelineData.normal.push(data.prediction === 0 ? 1 : 0);
    timelineData.anomaly.push(data.prediction === 1 ? 1 : 0);
    
    // Keep limited points
    while (timelineData.labels.length > MAX_TIMELINE_POINTS) {
        timelineData.labels.shift();
        timelineData.normal.shift();
        timelineData.anomaly.shift();
    }
    
    timelineChart.data.labels = timelineData.labels;
    timelineChart.data.datasets[0].data = timelineData.normal;
    timelineChart.data.datasets[1].data = timelineData.anomaly;
    timelineChart.update('none');
}

function updateTable(data) {
    const tbody = document.getElementById('liveTableBody');
    if (!tbody) return;
    
    const time = new Date().toLocaleTimeString();
    
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${time}</td>
        <td>#${data.sample_id}</td>
        <td>
            <span class="badge ${data.prediction === 1 ? 'bg-danger' : 'bg-success'}">
                ${data.label}
            </span>
        </td>
        <td>${(data.confidence * 100).toFixed(1)}%</td>
        <td>${data.physics_valid ? '✓' : '✗ (' + data.physics_violations + ')'}</td>
        <td>${data.ips_action || '-'}</td>
    `;
    
    tbody.insertBefore(row, tbody.firstChild);
    
    // Keep only limited rows to prevent infinite growth
    while (tbody.children.length > MAX_TABLE_ROWS) {
        tbody.removeChild(tbody.lastChild);
    }
}

function updateSHAP(data) {
    const container = document.getElementById('shapExplanation');
    
    if (!data.shap_top_features || data.prediction === 0) {
        container.innerHTML = '<p class="text-muted text-center">Waiting for anomaly detection...</p>';
        return;
    }
    
    let html = '';
    const maxShap = Math.max(...data.shap_top_features.map(f => Math.abs(f.shap_value)));
    
    for (const feature of data.shap_top_features) {
        const isPositive = feature.shap_value > 0;
        const barWidth = (Math.abs(feature.shap_value) / maxShap * 100).toFixed(0);
        
        html += `
            <div class="shap-feature">
                <span class="name">${feature.feature}</span>
                <div class="bar-container">
                    <div class="bar ${isPositive ? 'positive' : 'negative'}" 
                         style="width: ${barWidth}%"></div>
                </div>
                <span class="value ${isPositive ? 'text-danger' : 'text-success'}">
                    ${feature.shap_value.toFixed(3)}
                </span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function updateIPS(data) {
    const container = document.getElementById('ipsRecommendations');
    
    if (data.prediction === 0 || !data.ips_severity || data.ips_severity === 'none') {
        return; // Keep existing alerts visible
    }
    
    const severity = data.ips_severity;
    const icon = severity === 'critical' ? 'fa-skull-crossbones' : 
                 severity === 'high' ? 'fa-exclamation-circle' : 'fa-info-circle';
    
    // Get sample of affected features
    const features = data.shap_top_features ? 
        data.shap_top_features.slice(0, 3).map(f => f.feature).join(', ') : 'N/A';
    
    const alertHtml = `
        <div class="ips-alert ${severity}">
            <h6>
                <i class="fas ${icon}"></i>
                <span>${severity.toUpperCase()}</span>
                <small class="text-muted ms-auto">${new Date().toLocaleTimeString()}</small>
            </h6>
            <div class="small text-muted mb-2">
                Affected: ${features}
            </div>
            <div class="recommendations">
                <ul class="mb-0 ps-3">
                    <li>Verify sensor readings</li>
                    <li>Check network logs</li>
                    ${severity === 'critical' ? '<li class="text-danger">Auto-blocked by IPS</li>' : ''}
                </ul>
            </div>
        </div>
    `;
    
    container.innerHTML = alertHtml + container.innerHTML;
    
    // Keep only last 5 alerts
    while (container.children.length > 5) {
        container.removeChild(container.lastChild);
    }
}

function updateSCADAStatus(data) {
    const statusDiv = document.getElementById('scadaStatus');
    
    if (!data.shap_top_features || data.prediction === 0) {
        // Reset to OK status
        statusDiv.querySelectorAll('.status-indicator').forEach(el => {
            el.className = 'status-indicator normal';
            el.textContent = 'OK';
        });
        return;
    }
    
    // Check which components are affected
    const features = data.shap_top_features.map(f => f.feature);
    
    const tankAffected = features.some(f => f.startsWith('L_T'));
    const pumpAffected = features.some(f => f.startsWith('F_PU') || f.startsWith('S_PU'));
    const pressureAffected = features.some(f => f.startsWith('P_J'));
    
    const indicators = statusDiv.querySelectorAll('.scada-component');
    
    if (tankAffected) {
        indicators[0].querySelector('.status-indicator').className = 'status-indicator warning';
        indicators[0].querySelector('.status-indicator').textContent = 'ALERT';
    }
    
    if (pumpAffected) {
        indicators[1].querySelector('.status-indicator').className = 'status-indicator critical';
        indicators[1].querySelector('.status-indicator').textContent = 'CRITICAL';
    }
    
    if (pressureAffected) {
        indicators[2].querySelector('.status-indicator').className = 'status-indicator warning';
        indicators[2].querySelector('.status-indicator').textContent = 'ALERT';
    }
}
