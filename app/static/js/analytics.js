// ConvergeShield Analytics Page JavaScript
// Model metrics visualization and explainability

let featureImportanceChart = null;
let weightsChart = null;
let benchmarkChart = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Analytics page loaded, fetching metrics...');
    loadMetrics();
});

async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        if (!response.ok) {
            throw new Error('HTTP error: ' + response.status);
        }
        const data = await response.json();
        
        console.log('Metrics loaded:', data);
        
        if (data.error) {
            console.error('Metrics error:', data.error);
            return;
        }
        
        updateModelCards(data.model_metrics);
        updateConfusionMatrix(data.model_metrics.ensemble);
        createFeatureImportanceChart(data.feature_importance);
        createWeightsChart(data.model_weights);
        createBenchmarkChart(data.model_metrics);
        updateIPSStats(data.ips_statistics);
        
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

function updateModelCards(metrics) {
    console.log('Updating model cards with:', metrics);
    
    // Isolation Forest
    if (metrics.isolation_forest) {
        const ifAcc = document.getElementById('ifAccuracy');
        if (ifAcc) {
            const span = ifAcc.querySelector('span');
            if (span) span.textContent = (metrics.isolation_forest.accuracy * 100).toFixed(1) + '%';
        }
        setTextContent('ifPrecision', metrics.isolation_forest.precision.toFixed(3));
        setTextContent('ifRecall', metrics.isolation_forest.recall.toFixed(3));
        setTextContent('ifF1', metrics.isolation_forest.f1.toFixed(3));
    }
    
    // Random Forest
    if (metrics.random_forest) {
        const rfAcc = document.getElementById('rfAccuracy');
        if (rfAcc) {
            const span = rfAcc.querySelector('span');
            if (span) span.textContent = (metrics.random_forest.accuracy * 100).toFixed(1) + '%';
        }
        setTextContent('rfPrecision', metrics.random_forest.precision.toFixed(3));
        setTextContent('rfRecall', metrics.random_forest.recall.toFixed(3));
        setTextContent('rfF1', metrics.random_forest.f1.toFixed(3));
    }
    
    // XGBoost
    if (metrics.xgboost) {
        const xgbAcc = document.getElementById('xgbAccuracy');
        if (xgbAcc) {
            const span = xgbAcc.querySelector('span');
            if (span) span.textContent = (metrics.xgboost.accuracy * 100).toFixed(1) + '%';
        }
        setTextContent('xgbPrecision', metrics.xgboost.precision.toFixed(3));
        setTextContent('xgbRecall', metrics.xgboost.recall.toFixed(3));
        setTextContent('xgbF1', metrics.xgboost.f1.toFixed(3));
    }
    
    // Ensemble
    if (metrics.ensemble) {
        const ensAcc = document.getElementById('ensembleAccuracy');
        if (ensAcc) {
            const span = ensAcc.querySelector('span');
            if (span) span.textContent = (metrics.ensemble.accuracy * 100).toFixed(1) + '%';
        }
        setTextContent('ensemblePrecision', metrics.ensemble.precision.toFixed(3));
        setTextContent('ensembleRecall', metrics.ensemble.recall.toFixed(3));
        setTextContent('ensembleF1', metrics.ensemble.f1.toFixed(3));
        if (metrics.ensemble.auc) {
            setTextContent('ensembleAuc', metrics.ensemble.auc.toFixed(3));
        }
    }
}

function setTextContent(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function updateConfusionMatrix(ensembleMetrics) {
    if (!ensembleMetrics || !ensembleMetrics.confusion_matrix) return;
    
    const cm = ensembleMetrics.confusion_matrix;
    // [[TN, FP], [FN, TP]]
    document.getElementById('cmTN').textContent = cm[0][0];
    document.getElementById('cmFP').textContent = cm[0][1];
    document.getElementById('cmFN').textContent = cm[1][0];
    document.getElementById('cmTP').textContent = cm[1][1];
}

function createFeatureImportanceChart(featureImportance) {
    if (!featureImportance || featureImportance.length === 0) return;
    
    const ctx = document.getElementById('featureImportanceChart').getContext('2d');
    
    // Sort and take top 15
    const sorted = [...featureImportance].sort((a, b) => b[1] - a[1]).slice(0, 15);
    const labels = sorted.map(f => f[0]);
    const values = sorted.map(f => f[1]);
    
    // Color based on feature type
    const colors = labels.map(label => {
        if (label.startsWith('L_T')) return 'rgba(59, 130, 246, 0.7)';  // Tank - blue
        if (label.startsWith('F_PU') || label.startsWith('S_PU')) return 'rgba(245, 158, 11, 0.7)';  // Pump - orange
        if (label.startsWith('P_J')) return 'rgba(16, 185, 129, 0.7)';  // Pressure - green
        return 'rgba(139, 92, 246, 0.7)';  // Other - purple
    });
    
    featureImportanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Importance',
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: '#2d3a4f' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af', font: { size: 11 } }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function createWeightsChart(weights) {
    if (!weights) return;
    
    const ctx = document.getElementById('weightsChart').getContext('2d');
    
    weightsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Isolation Forest', 'Random Forest', 'XGBoost'],
            datasets: [{
                data: [
                    weights.isolation_forest * 100,
                    weights.random_forest * 100,
                    weights.xgboost * 100
                ],
                backgroundColor: [
                    'rgba(245, 158, 11, 0.7)',
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ],
                borderColor: [
                    '#f59e0b',
                    '#3b82f6',
                    '#8b5cf6'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#e5e7eb' }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.toFixed(0) + '%';
                        }
                    }
                }
            }
        }
    });
}

function createBenchmarkChart(metrics) {
    const ctx = document.getElementById('benchmarkChart').getContext('2d');
    
    // Reference paper benchmarks (from the problem statement)
    const benchmarks = {
        'OCSVM (Paper)': { f1: 0.91, accuracy: 0.9332 },
        'IF (Paper)': { f1: 0.13, accuracy: 0.6302 },
        'CSAD (Paper)': { f1: 0.20, accuracy: 0.66 }
    };
    
    const labels = ['IF (Paper)', 'IF (Ours)', 'RF (Ours)', 'XGBoost (Ours)', 'Ensemble (Ours)'];
    const f1Scores = [
        benchmarks['IF (Paper)'].f1,
        metrics.isolation_forest ? metrics.isolation_forest.f1 : 0,
        metrics.random_forest ? metrics.random_forest.f1 : 0,
        metrics.xgboost ? metrics.xgboost.f1 : 0,
        metrics.ensemble ? metrics.ensemble.f1 : 0
    ];
    
    benchmarkChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'F1 Score',
                data: f1Scores,
                backgroundColor: [
                    'rgba(156, 163, 175, 0.5)',  // Paper benchmark (gray)
                    'rgba(245, 158, 11, 0.7)',
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(139, 92, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)'
                ],
                borderColor: [
                    '#9ca3af',
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
                    ticks: { color: '#9ca3af', font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'F1 Score Comparison (Higher is Better)',
                    color: '#9ca3af',
                    font: { size: 12 }
                }
            }
        }
    });
}

function updateIPSStats(stats) {
    if (!stats) return;
    
    document.getElementById('totalAlerts').textContent = stats.total_alerts || 0;
    document.getElementById('criticalAlerts').textContent = stats.by_severity?.critical || 0;
    document.getElementById('highAlerts').textContent = stats.by_severity?.high || 0;
    document.getElementById('mediumAlerts').textContent = stats.by_severity?.medium || 0;
    document.getElementById('autoBlocked').textContent = stats.blocked || 0;
}
