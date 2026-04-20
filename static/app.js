let currentTab = 'login';
let charts = {};

// UI State Management
function switchAuthTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    const activeTab = document.querySelector(`.tab[onclick="switchAuthTab('${tab}')"]`);
    if (activeTab) activeTab.classList.add('active');
    
    document.getElementById('auth-btn').textContent = tab === 'login' ? 'Login' : 'Register';
    document.getElementById('auth-error').textContent = '';
}

function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
    
    if (viewId === 'dashboard-view') {
        loadDashboardData();
    }
}

// Authentication
async function handleAuth(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('auth-error');
    errorEl.textContent = '';

    try {
        if (currentTab === 'register') {
            const res = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            if (!res.ok) throw new Error((await res.json()).detail || 'Registration failed');
            // Switch to login tab after successful registration
            switchAuthTab('login');
            document.querySelector('.tab[onclick="switchAuthTab(\'login\')"]').classList.add('active');
            document.querySelector('.tab[onclick="switchAuthTab(\'register\')"]').classList.remove('active');
            errorEl.style.color = 'var(--accent)';
            errorEl.textContent = 'Registration successful! Please login.';
        } else {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch('/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            if (!res.ok) throw new Error('Invalid credentials');
            const data = await res.json();
            localStorage.setItem('token', data.access_token);
            showView('dashboard-view');
        }
    } catch (err) {
        errorEl.style.color = 'var(--error)';
        errorEl.textContent = err.message;
    }
}

function logout() {
    localStorage.removeItem('token');
    showView('auth-view');
    document.getElementById('password').value = '';
}

// Check initial auth state
if (localStorage.getItem('token')) {
    showView('dashboard-view');
} else {
    showView('auth-view');
}

// Upload Handling
async function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    const statusEl = document.getElementById('upload-status');
    statusEl.style.color = 'var(--text-main)';
    statusEl.textContent = 'Processing image with AI... please wait.';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });

        if (res.status === 401) { logout(); return; }
        if (!res.ok) {
            let errorMsg = 'Upload failed';
            try {
                const errData = await res.json();
                if (errData.detail) errorMsg = errData.detail;
            } catch (e) {}
            throw new Error(errorMsg);
        }
        
        statusEl.style.color = 'var(--accent)';
        statusEl.textContent = 'Successfully extracted and saved data!';
        loadDashboardData(); // Refresh charts
        
    } catch (err) {
        statusEl.style.color = 'var(--error)';
        statusEl.textContent = err.message;
    }
    
    // Reset file input
    e.target.value = '';
}

// Drag and drop visual cues
const dropZone = document.getElementById('drop-zone');
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--primary-color)';
});
dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = 'var(--border-color)';
});
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--border-color)';
    if (e.dataTransfer.files.length) {
        document.getElementById('file-input').files = e.dataTransfer.files;
        handleFileSelect({ target: { files: e.dataTransfer.files } });
    }
});

let chartInstance = null;
let dashboardData = [];

// Load Users
async function loadUsers() {
    try {
        const res = await fetch('/api/users', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (res.ok) {
            const users = await res.json();
            const selector = document.getElementById('userSelector');
            const currentVal = selector.value;
            selector.innerHTML = '';
            users.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.textContent = "Data of: " + u.username;
                selector.appendChild(opt);
            });
            // Try to keep previous selection, otherwise it defaults to first
            if (currentVal && Array.from(selector.options).some(o => o.value === currentVal)) {
                selector.value = currentVal;
            }
        }
    } catch (err) {
        console.error('Failed to load users', err);
    }
}

// Load and Render Data
async function loadDashboardData() {
    try {
        await loadUsers(); // Refresh users list
        
        let url = '/api/data';
        const userId = document.getElementById('userSelector').value;
        if (userId) {
            url += `?user_id=${userId}`;
        }
        
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (res.status === 401) { logout(); return; }
        const data = await res.json();
        dashboardData = data;
        renderStatsGrid(data);
    } catch (err) {
        console.error('Failed to load data', err);
    }
}

function renderStatsGrid(data) {
    if (!data || data.length === 0) return;
    const latest = data[data.length - 1]; // Newest record
    
    const metrics = [
        { key: 'body_score', label: 'Body score', unit: ' points' },
        { key: 'bmi', label: 'BMI', unit: '' },
        { key: 'body_fat_percentage', label: 'Body fat percentage', unit: '%' },
        { key: 'body_water_mass', label: 'Body water mass', unit: 'kg' },
        { key: 'fat_mass', label: 'Fat mass', unit: 'kg' },
        { key: 'bone_mineral_mass', label: 'Bone mineral mass', unit: 'kg' },
        { key: 'protein_mass', label: 'Protein mass', unit: 'kg' },
        { key: 'muscle_mass', label: 'Muscle mass', unit: 'kg' },
        { key: 'muscle_percentage', label: 'Muscle percentage', unit: '%' },
        { key: 'body_water_percentage', label: 'Body water', unit: '%' },
        { key: 'protein_percentage', label: 'Protein percentage', unit: '%' },
        { key: 'bone_mineral_percentage', label: 'Bone mineral percentage', unit: '%' },
        { key: 'skeletal_muscle_mass', label: 'Skeletal muscle mass', unit: 'kg' },
        { key: 'visceral_fat_rating', label: 'Visceral fat rating', unit: '' },
        { key: 'basal_metabolic_rate', label: 'Basal metabolic rate', unit: ' kcal' },
        { key: 'estimated_waist_to_hip_ratio', label: 'Estimated waist-to-hip ratio', unit: '' },
        { key: 'body_age', label: 'Body age', unit: ' years old' },
        { key: 'fat_free_body_weight', label: 'Fat-free body weight', unit: 'kg' },
        { key: 'heart_rate', label: 'Heart rate', unit: ' bpm' }
    ];

    const grid = document.getElementById('statsGrid');
    grid.innerHTML = '';
    
    // Create large main card for weight
    const weightCard = document.createElement('div');
    weightCard.className = 'stat-card glass';
    weightCard.style.gridColumn = '1 / -1'; // span full width
    weightCard.style.textAlign = 'center';
    weightCard.style.alignItems = 'center';
    weightCard.innerHTML = `
        <div class="stat-label" style="font-size:1.2rem; margin-bottom:1rem;">Body Weight</div>
        <div class="stat-value" style="font-size:4rem; color:white;">${latest.body_weight || '--'}<span class="stat-unit" style="font-size:1.5rem;">kg</span></div>
    `;
    weightCard.onclick = () => openTrendModal('body_weight', 'Body Weight Trend');
    grid.appendChild(weightCard);

    // Create cards for the rest of the metrics
    metrics.forEach(m => {
        const val = (latest[m.key] !== null && latest[m.key] !== undefined) ? latest[m.key] : '--';
        const card = document.createElement('div');
        card.className = 'stat-card glass';
        card.innerHTML = `
            <div class="stat-value">${val}<span class="stat-unit">${m.unit}</span></div>
            <div class="stat-label">${m.label}</div>
        `;
        card.onclick = () => openTrendModal(m.key, m.label + ' Trend');
        grid.appendChild(card);
    });
}

function openTrendModal(metricKey, title) {
    document.getElementById('chartModal').classList.remove('hidden');
    document.getElementById('modalChartTitle').textContent = title;
    
    if (chartInstance) chartInstance.destroy();
    
    const labels = dashboardData.map(d => new Date(d.date));
    const values = dashboardData.map(d => d[metricKey]);
    
    const ctx = document.getElementById('modalChart').getContext('2d');
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Inter';
    
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { 
                    type: 'time', 
                    time: { tooltipFormat: 'll' }, 
                    grid: { color: 'rgba(255,255,255,0.05)' } 
                },
                y: { 
                    grid: { color: 'rgba(255,255,255,0.05)' } 
                }
            },
            plugins: { 
                legend: { display: false } 
            }
        }
    });
}

function closeModal() {
    document.getElementById('chartModal').classList.add('hidden');
}
