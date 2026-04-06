// ConvergeShield Incident Explorer JavaScript
// Incident management and filtering

let incidentsData = [];
let dataTable = null;

document.addEventListener('DOMContentLoaded', function() {
    initDataTable();
    loadIncidents();
    
    // Update confidence display
    document.getElementById('filterConfidence').addEventListener('input', function() {
        document.getElementById('confidenceValue').textContent = this.value;
    });
});

function initDataTable() {
    dataTable = $('#incidentsTable').DataTable({
        order: [[0, 'desc']],
        pageLength: 25,
        language: {
            emptyTable: "No incidents recorded yet. Start monitoring from Dashboard.",
            search: "Search:",
            lengthMenu: "Show _MENU_ incidents"
        },
        columnDefs: [
            { targets: [6], orderable: false }
        ]
    });
}

async function loadIncidents() {
    try {
        const response = await fetch('/api/ips/stats');
        const data = await response.json();
        
        if (data.recent_alerts && data.recent_alerts.length > 0) {
            incidentsData = data.recent_alerts;
            renderIncidents();
            updateStats(data);
        }
    } catch (error) {
        console.error('Failed to load incidents:', error);
    }
}

function renderIncidents() {
    dataTable.clear();
    
    incidentsData.forEach((incident, index) => {
        const severityBadge = getSeverityBadge(incident.severity);
        const actionBadge = incident.action === 'BLOCK' ? 
            '<span class="badge bg-danger">BLOCKED</span>' : 
            '<span class="badge bg-warning">ALERT</span>';
        const physicsBadge = incident.physics_valid !== false ? 
            '<span class="badge bg-success">✓</span>' : 
            '<span class="badge bg-warning">✗</span>';
        
        const row = [
            formatTimestamp(incident.timestamp),
            severityBadge,
            formatAttackType(incident.attack_type),
            `${(incident.confidence * 100).toFixed(1)}%`,
            physicsBadge,
            actionBadge,
            `<button class="btn btn-sm btn-outline-info" onclick="showDetails(${index})">
                <i class="fas fa-eye"></i>
            </button>`
        ];
        
        dataTable.row.add(row);
    });
    
    dataTable.draw();
    document.getElementById('visibleCount').textContent = `${incidentsData.length} visible`;
}

function getSeverityBadge(severity) {
    const colors = {
        critical: 'bg-danger',
        high: 'bg-warning',
        medium: 'bg-info',
        low: 'bg-secondary'
    };
    return `<span class="badge ${colors[severity] || 'bg-secondary'}">${severity?.toUpperCase() || 'UNKNOWN'}</span>`;
}

function formatAttackType(type) {
    if (!type) return 'Unknown';
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatTimestamp(ts) {
    if (!ts) return '-';
    const date = new Date(ts);
    return date.toLocaleString();
}

function updateStats(data) {
    document.getElementById('totalIncidents').textContent = data.total_alerts || 0;
    document.getElementById('criticalCount').textContent = data.by_severity?.critical || 0;
    document.getElementById('highCount').textContent = data.by_severity?.high || 0;
    document.getElementById('mediumCount').textContent = data.by_severity?.medium || 0;
    document.getElementById('blockedCount').textContent = data.blocked || 0;
}

function filterTable() {
    const severity = document.getElementById('filterSeverity').value.toLowerCase();
    const attack = document.getElementById('filterAttack').value;
    const action = document.getElementById('filterAction').value;
    const minConfidence = parseInt(document.getElementById('filterConfidence').value) / 100;
    
    // Custom DataTables filtering
    $.fn.dataTable.ext.search.pop(); // Remove previous filter
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        const incident = incidentsData[dataIndex];
        if (!incident) return true;
        
        if (severity && incident.severity !== severity) return false;
        if (attack && incident.attack_type !== attack) return false;
        if (action && incident.action !== action) return false;
        if (incident.confidence < minConfidence) return false;
        
        return true;
    });
    
    dataTable.draw();
    
    const visibleRows = dataTable.rows({ search: 'applied' }).count();
    document.getElementById('visibleCount').textContent = `${visibleRows} visible`;
}

function showDetails(index) {
    const incident = incidentsData[index];
    if (!incident) return;
    
    const recommendations = incident.recommendations || ['Investigate the anomaly', 'Check system logs'];
    const affectedComponents = incident.affected_components || [];
    
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-muted">Incident Information</h6>
                <table class="table table-dark table-sm">
                    <tr>
                        <td>Timestamp:</td>
                        <td>${formatTimestamp(incident.timestamp)}</td>
                    </tr>
                    <tr>
                        <td>Severity:</td>
                        <td>${getSeverityBadge(incident.severity)}</td>
                    </tr>
                    <tr>
                        <td>Attack Type:</td>
                        <td>${formatAttackType(incident.attack_type)}</td>
                    </tr>
                    <tr>
                        <td>Confidence:</td>
                        <td>
                            <div class="progress" style="height: 20px;">
                                <div class="progress-bar ${incident.confidence > 0.7 ? 'bg-danger' : 'bg-warning'}" 
                                     style="width: ${incident.confidence * 100}%">
                                    ${(incident.confidence * 100).toFixed(1)}%
                                </div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>Action Taken:</td>
                        <td>${incident.action === 'BLOCK' ? 
                            '<span class="badge bg-danger">AUTO-BLOCKED</span>' : 
                            '<span class="badge bg-warning">ALERT RAISED</span>'}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6 class="text-muted">Attack Description</h6>
                <p class="small">${incident.attack_description || 'Anomalous behavior detected in the system.'}</p>
                
                <h6 class="text-muted mt-3">Affected Components</h6>
                <div class="mb-3">
                    ${affectedComponents.length > 0 ? 
                        affectedComponents.map(c => `<span class="badge bg-secondary me-1">${c}</span>`).join('') :
                        '<span class="text-muted small">No specific components identified</span>'}
                </div>
            </div>
        </div>
        
        <hr class="border-secondary">
        
        <h6 class="text-muted"><i class="fas fa-lightbulb me-2"></i>Recommendations</h6>
        <ul class="list-group list-group-flush bg-transparent">
            ${recommendations.map(r => `
                <li class="list-group-item bg-transparent text-light border-secondary">
                    <i class="fas fa-chevron-right me-2 text-info"></i>${r}
                </li>
            `).join('')}
        </ul>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('incidentModal'));
    modal.show();
}

async function clearIncidents() {
    if (!confirm('Are you sure you want to clear all incidents?')) return;
    
    try {
        await fetch('/api/ips/clear', { method: 'POST' });
        incidentsData = [];
        renderIncidents();
        updateStats({ total_alerts: 0, by_severity: {}, blocked: 0 });
    } catch (error) {
        console.error('Failed to clear incidents:', error);
    }
}

function exportIncidents() {
    if (incidentsData.length === 0) {
        alert('No incidents to export');
        return;
    }
    
    const headers = ['Timestamp', 'Severity', 'Attack Type', 'Confidence', 'Action', 'Description'];
    const rows = incidentsData.map(i => [
        i.timestamp,
        i.severity,
        i.attack_type,
        i.confidence,
        i.action,
        i.attack_description
    ]);
    
    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        csv += row.map(cell => `"${cell || ''}"`).join(',') + '\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `convergeshield_incidents_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
}

function acknowledgeIncident() {
    alert('Incident acknowledged. In production, this would update the incident status.');
    bootstrap.Modal.getInstance(document.getElementById('incidentModal')).hide();
}

// Auto-refresh every 10 seconds
setInterval(loadIncidents, 10000);
