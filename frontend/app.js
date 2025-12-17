// State
let videos = {};
let analysisResults = {};
let socket = null;
let analysisInterval = null;
let analysis_running = false;
let vehicleChart = null;
let trafficPieChart = null;
let trafficHistory = { timestamps: [], lanes: {1: [], 2: [], 3: [], 4: []} };

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupVideoUploads();
    setupAnalyzeButton();
    connectWebSocket();
    initializeCharts();
    initializeBlockchain();
    addSystemLog('info', 'System initialized');
});

// Setup video file uploads
function setupVideoUploads() {
    for (let i = 1; i <= 4; i++) {
        const input = document.getElementById(`video${i}`);
        const preview = document.getElementById(`preview${i}`);
        const card = document.getElementById(`card${i}`);
        const removeBtn = document.getElementById(`remove${i}`);
        
        // File input change handler
        input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                videos[i] = file;
                card.classList.add('has-video');
                
                // Show preview
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.controls = true;
                video.style.width = '100%';
                preview.innerHTML = '';
                preview.appendChild(video);
                preview.classList.add('show');
                
                // Show remove button
                removeBtn.style.display = 'block';
                
                // Upload to backend
                uploadVideo(i, file);
            }
            checkAllVideosUploaded();
        });
        
        // Remove button handler
        removeBtn.addEventListener('click', () => {
            removeVideo(i);
        });
    }
}

// Upload video to backend
async function uploadVideo(laneId, file) {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('lane_id', laneId);
    
    try {
        const response = await fetch(`http://localhost:5000/api/upload-video`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Video ${laneId} uploaded successfully:`, data);
            // Store video URL for later use
            if (!analysisResults.lanes) {
                analysisResults.lanes = [];
            }
            const existingLane = analysisResults.lanes.find(l => l.lane_id === laneId);
            if (existingLane) {
                existingLane.video_url = data.video_url;
            } else {
                analysisResults.lanes.push({
                    lane_id: laneId,
                    video_url: data.video_url,
                    vehicle_count: 0,
                    green_time: 30,
                    is_green: false,
                    detection_boxes: []
                });
            }
        } else {
            const error = await response.json();
            console.error(`Error uploading video ${laneId}:`, error);
        }
    } catch (error) {
        console.error(`Error uploading video ${laneId}:`, error);
    }
}

// Remove video
async function removeVideo(laneId) {
    // Confirm removal
    if (!confirm(`Are you sure you want to remove the video for Lane ${laneId}?`)) {
        return;
    }
    
    // If analysis is running, stop it first
    if (analysis_running) {
        try {
            await fetch('http://localhost:5000/api/stop-analysis', {
                method: 'POST'
            });
            analysis_running = false;
        } catch (error) {
            console.error('Error stopping analysis:', error);
        }
    }
    
    // Remove from local state
    delete videos[laneId];
    
    // Reset UI
    const input = document.getElementById(`video${laneId}`);
    const preview = document.getElementById(`preview${laneId}`);
    const card = document.getElementById(`card${laneId}`);
    const removeBtn = document.getElementById(`remove${laneId}`);
    
    input.value = '';
    preview.innerHTML = '';
    preview.classList.remove('show');
    card.classList.remove('has-video');
    removeBtn.style.display = 'none';
    
    // Delete from backend
    try {
        const response = await fetch(`http://localhost:5000/api/remove-video/${laneId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            console.log(`Video ${laneId} removed successfully`);
            
            // If we're in results view, hide it and show upload section
            const resultsSection = document.getElementById('results-section');
            const uploadSection = document.getElementById('upload-section');
            if (resultsSection && resultsSection.style.display !== 'none') {
                resultsSection.style.display = 'none';
                uploadSection.style.display = 'block';
            }
        } else {
            const error = await response.json();
            alert(`Error removing video: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error(`Error removing video ${laneId}:`, error);
        alert(`Error removing video: ${error.message}`);
    }
    
    // Update analyze button state
    checkAllVideosUploaded();
}

// Check if all videos are uploaded
function checkAllVideosUploaded() {
    const allUploaded = Object.keys(videos).length === 4;
    const analyzeBtn = document.getElementById('analyze-btn');
    analyzeBtn.disabled = !allUploaded;
}

// Setup analyze button
function setupAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyze-btn');
    analyzeBtn.addEventListener('click', () => {
        startAnalysis();
    });
}

// Start analysis
async function startAnalysis() {
    const analyzeBtn = document.getElementById('analyze-btn');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
    
    document.getElementById('upload-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    
    analysis_running = true;
    emergencyNotified = {};  // Reset emergency notifications when starting new analysis
    
    // Start analysis on backend
    try {
        const response = await fetch('http://localhost:5000/api/start-analysis', {
            method: 'POST'
        });
        
        if (response.ok) {
            console.log('Analysis started');
            updateAnalysisStatus('Analyzing videos...');
            addSystemLog('success', 'Analysis started for all lanes');
        }
    } catch (error) {
        console.error('Error starting analysis:', error);
        analysis_running = false;
    }
}

// Connect WebSocket for real-time updates
function connectWebSocket() {
    socket = io('http://localhost:5000');
    
    socket.on('connect', () => {
        console.log('Connected to server');
        addSystemLog('success', 'Connected to server');
    });
    
    socket.on('analysis_update', (data) => {
        if (data.status === 'running') {
            analysis_running = true;
        }
        updateAnalysisResults(data);
    });
    
    socket.on('traffic_update', (data) => {
        updateTrafficLights(data);
    });
    
    socket.on('traffic_data', (data) => {
        updateTrafficCharts(data);
    });
    
    socket.on('system_log', (log) => {
        addSystemLog(log.level, log.message, log.timestamp);
    });
    
    // Blockchain real-time updates
    socket.on('blockchain_transaction', (data) => {
        // Refresh blockchain data when new transaction is added
        if (analysis_running) {
            loadBlockchainStats();
            loadBlockchainTransactions();
        }
    });
    
    socket.on('blockchain_block_mined', (data) => {
        // Refresh blockchain data when new block is mined
        if (analysis_running) {
            loadBlockchainStats();
            loadBlockchainTransactions();
        }
    });
}

// Initialize Charts
function initializeCharts() {
    // Vehicle Count Over Time Chart
    const vehicleCtx = document.getElementById('vehicle-chart');
    if (vehicleCtx) {
        vehicleChart = new Chart(vehicleCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Lane 1', data: [], borderColor: '#2196F3', backgroundColor: 'rgba(33, 150, 243, 0.1)' },
                    { label: 'Lane 2', data: [], borderColor: '#4CAF50', backgroundColor: 'rgba(76, 175, 80, 0.1)' },
                    { label: 'Lane 3', data: [], borderColor: '#FF9800', backgroundColor: 'rgba(255, 152, 0, 0.1)' },
                    { label: 'Lane 4', data: [], borderColor: '#9C27B0', backgroundColor: 'rgba(156, 39, 176, 0.1)' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Vehicle Count' } },
                    x: { title: { display: true, text: 'Time' } }
                }
            }
        });
    }
    
    // Traffic Distribution Pie Chart
    const pieCtx = document.getElementById('traffic-pie-chart');
    if (pieCtx) {
        trafficPieChart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Lane 1', 'Lane 2', 'Lane 3', 'Lane 4'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
}

// Update Traffic Charts
function updateTrafficCharts(data) {
    if (!data || !data.lanes) return;
    
    const now = new Date().toLocaleTimeString();
    
    // Update line chart
    if (vehicleChart) {
        vehicleChart.data.labels.push(now);
        vehicleChart.data.datasets[0].data.push(data.lanes[1] || 0);
        vehicleChart.data.datasets[1].data.push(data.lanes[2] || 0);
        vehicleChart.data.datasets[2].data.push(data.lanes[3] || 0);
        vehicleChart.data.datasets[3].data.push(data.lanes[4] || 0);
        
        // Keep only last 20 data points
        if (vehicleChart.data.labels.length > 20) {
            vehicleChart.data.labels.shift();
            vehicleChart.data.datasets.forEach(dataset => dataset.data.shift());
        }
        
        vehicleChart.update('none');
    }
    
    // Update pie chart
    if (trafficPieChart) {
        const total = (data.lanes[1] || 0) + (data.lanes[2] || 0) + (data.lanes[3] || 0) + (data.lanes[4] || 0);
        if (total > 0) {
            trafficPieChart.data.datasets[0].data = [
                data.lanes[1] || 0,
                data.lanes[2] || 0,
                data.lanes[3] || 0,
                data.lanes[4] || 0
            ];
            trafficPieChart.update('none');
        }
    }
}

// Add System Log
function addSystemLog(level, message, timestamp = null) {
    const logsContainer = document.getElementById('system-logs');
    if (!logsContainer) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const time = timestamp || new Date().toLocaleTimeString();
    
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-level ${level}">[${level.toUpperCase()}]</span>
        <span class="log-message">${message}</span>
    `;
    
    logsContainer.appendChild(logEntry);
    
    // Auto-scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;
    
    // Keep only last 100 logs
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.firstChild);
    }
}

// Clear Logs
function clearLogs() {
    const logsContainer = document.getElementById('system-logs');
    if (logsContainer) {
        logsContainer.innerHTML = '';
        addSystemLog('info', 'Logs cleared');
    }
}

// Update analysis results
function updateAnalysisResults(data) {
    analysisResults = data;
    
    // Update status
    if (data.status === 'complete') {
        updateAnalysisStatus('Analysis Complete');
    }
    
    // Update video grid
    if (data.lanes) {
        updateVideoGrid(data.lanes);
        
        // Update detection boxes disabled to prevent loading issues
        // data.lanes.forEach(lane => {
        //     updateDetectionBoxes(lane.lane_id);
        // });
    }
    
    // Update statistics
    updateStatistics(data);
    
    // Update traffic lights
    updateTrafficLights(data);
}

// Update video grid
function updateVideoGrid(lanes) {
    const grid = document.getElementById('video-grid');
    
    // Check if grid is already populated
    const existingCards = grid.querySelectorAll('.video-analysis-card');
    
    if (existingCards.length === 0) {
        // First time: create all video elements
        lanes.forEach(lane => {
            const card = document.createElement('div');
            card.className = 'video-analysis-card';
            card.id = `video-card-${lane.lane_id}`;
            
            const lightStatus = lane.is_green ? 'green' : 'red';
            const lightEmoji = lightStatus === 'green' ? '🟢' : '🔴';
            
            if (lane.is_green) {
                card.classList.add('highest-traffic', 'green-light');
            } else {
                card.classList.add('red-light');
            }
            
            card.innerHTML = `
                <div class="video-header">
                    <span class="video-title">Lane ${lane.lane_id}</span>
                    <div class="traffic-light-indicator ${lightStatus}" id="light-indicator-${lane.lane_id}">${lightEmoji}</div>
                </div>
                <div class="video-container" id="video-container-${lane.lane_id}">
                    <video id="video-${lane.lane_id}" src="http://localhost:5000${lane.video_url}" controls autoplay loop muted playsinline></video>
                    <div class="video-overlay" id="overlay-${lane.lane_id}">
                        <div>Vehicles: ${lane.vehicle_count}</div>
                    </div>
                </div>
                <div class="video-stats" id="stats-${lane.lane_id}">
                    <div class="stat-box">
                        <div class="stat-label">Vehicle Count</div>
                        <div class="stat-value vehicles" id="vehicle-count-${lane.lane_id}">${lane.vehicle_count}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Detections</div>
                        <div class="stat-value" style="color: #2196F3;" id="detections-${lane.lane_id}">${(lane.detection_boxes || []).length}</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Signal Status</div>
                        <div class="stat-value" id="signal-status-${lane.lane_id}" style="color: ${lightStatus === 'green' ? '#4CAF50' : '#f44336'};">
                            ${lightStatus.toUpperCase()}
                        </div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Green Time</div>
                        <div class="stat-value" style="color: #667eea;" id="green-time-${lane.lane_id}">${lane.green_time}s</div>
                    </div>
                </div>
            `;
            
            grid.appendChild(card);
            
            // Ensure video autoplays and loops continuously
            setTimeout(() => {
                const video = document.getElementById(`video-${lane.lane_id}`);
                if (video) {
                    video.loop = true;
                    video.muted = true;
                    video.playsInline = true;
                    if (video.paused) {
                        video.play().catch(e => console.log('Autoplay prevented:', e));
                    }
                }
            }, 100);
        });
    } else {
        // Update existing cards without recreating video elements
        lanes.forEach(lane => {
            const lightStatus = lane.is_green ? 'green' : 'red';
            const lightEmoji = lightStatus === 'green' ? '🟢' : '🔴';
            
            // Update card classes
            const card = document.getElementById(`video-card-${lane.lane_id}`);
            if (card) {
                card.className = 'video-analysis-card';
                if (lane.is_green) {
                    card.classList.add('highest-traffic', 'green-light');
                } else {
                    card.classList.add('red-light');
                }
                
                // Update light indicator
                const lightIndicator = document.getElementById(`light-indicator-${lane.lane_id}`);
                if (lightIndicator) {
                    lightIndicator.className = `traffic-light-indicator ${lightStatus}`;
                    lightIndicator.textContent = lightEmoji;
                }
                
                // Update overlay
                const overlay = document.getElementById(`overlay-${lane.lane_id}`);
                if (overlay) {
                    overlay.innerHTML = `<div>Vehicles: ${lane.vehicle_count}</div>`;
                }
                
                // Update stats
                const vehicleCountEl = document.getElementById(`vehicle-count-${lane.lane_id}`);
                if (vehicleCountEl) vehicleCountEl.textContent = lane.vehicle_count;
                
                const detectionsEl = document.getElementById(`detections-${lane.lane_id}`);
                if (detectionsEl) detectionsEl.textContent = (lane.detection_boxes || []).length;
                
                const signalStatusEl = document.getElementById(`signal-status-${lane.lane_id}`);
                if (signalStatusEl) {
                    signalStatusEl.textContent = lightStatus.toUpperCase();
                    signalStatusEl.style.color = lightStatus === 'green' ? '#4CAF50' : '#f44336';
                }
                
                const greenTimeEl = document.getElementById(`green-time-${lane.lane_id}`);
                if (greenTimeEl) greenTimeEl.textContent = `${lane.green_time}s`;
                
                // Ensure video continues playing
                const video = document.getElementById(`video-${lane.lane_id}`);
                if (video && video.paused) {
                    video.play().catch(e => console.log('Autoplay prevented:', e));
                }
            }
        });
    }
}

// Setup video with detection boxes - DISABLED to prevent loading issues
function setupVideoWithDetections(laneId, videoUrl, detectionBoxes) {
    // Bounding boxes disabled - this function is now a no-op
    // Canvas drawing was causing continuous video reloading
    return;
    
    /* ORIGINAL CODE - DISABLED
    const video = document.getElementById(`video-${laneId}`);
    const canvas = document.getElementById(`canvas-${laneId}`);
    
    if (!video || !canvas) {
        setTimeout(() => setupVideoWithDetections(laneId, videoUrl, detectionBoxes), 100);
        return;
    }
    
    const updateCanvas = () => {
        if (video.readyState >= 2) {
            const rect = video.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            
            const lane = analysisResults.lanes?.find(l => l.lane_id === laneId);
            const boxes = lane?.detection_boxes || detectionBoxes || [];
            
            if (video.videoWidth > 0 && video.videoHeight > 0) {
                drawDetectionBoxes(canvas, boxes, video.videoWidth, video.videoHeight, rect.width, rect.height);
            }
        }
    };
    
    video.addEventListener('loadedmetadata', updateCanvas);
    video.addEventListener('loadeddata', updateCanvas);
    video.addEventListener('resize', updateCanvas);
    
    let updateInterval = null;
    video.addEventListener('play', () => {
        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(() => {
            if (video.paused || video.ended) {
                clearInterval(updateInterval);
                updateInterval = null;
            } else {
                updateCanvas();
            }
        }, 1000);
    });
    
    video.addEventListener('pause', () => {
        if (updateInterval) {
            clearInterval(updateInterval);
            updateInterval = null;
        }
    });
    */
}

// Draw detection boxes on canvas - DISABLED to prevent loading issues
function drawDetectionBoxes(canvas, boxes, videoWidth, videoHeight, canvasWidth, canvasHeight) {
    // Bounding boxes disabled - this function is now a no-op
    // Drawing boxes was causing continuous video reloading
    return;
    
    /* ORIGINAL CODE - DISABLED
    if (!canvas || !boxes || boxes.length === 0) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
    }
    
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const scaleX = canvasWidth / videoWidth;
    const scaleY = canvasHeight / videoHeight;
    
    boxes.forEach(box => {
        const x = (box.x / 100) * videoWidth * scaleX;
        const y = (box.y / 100) * videoHeight * scaleY;
        const width = (box.width / 100) * videoWidth * scaleX;
        const height = (box.height / 100) * videoHeight * scaleY;
        
        ctx.strokeStyle = '#00FF00';
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, width, height);
        
        const label = `${box.class} ${(box.confidence * 100).toFixed(0)}%`;
        ctx.fillStyle = 'rgba(0, 255, 0, 0.8)';
        ctx.font = 'bold 14px Arial';
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(x, Math.max(0, y - 22), textWidth + 10, 22);
        
        ctx.fillStyle = '#000';
        ctx.fillText(label, x + 5, Math.max(14, y - 5));
    });
    */
}

// Update detection boxes periodically - DISABLED to prevent loading issues
function updateDetectionBoxes(laneId) {
    // Bounding boxes disabled - this function is now a no-op
    return;
    
    /* ORIGINAL CODE - DISABLED
    const lane = analysisResults.lanes?.find(l => l.lane_id === laneId);
    if (!lane) return;
    
    const canvas = document.getElementById(`canvas-${laneId}`);
    const video = document.getElementById(`video-${laneId}`);
    
    if (canvas && video && video.videoWidth > 0) {
        const container = video.parentElement;
        drawDetectionBoxes(canvas, lane.detection_boxes || [], video.videoWidth, video.videoHeight, container.offsetWidth, container.offsetHeight);
    }
    */
}

// Update traffic lights panel
function updateTrafficLights(data) {
    const lightsContainer = document.getElementById('traffic-lights');
    lightsContainer.innerHTML = '';
    
    const lanes = data.lanes || analysisResults.lanes || [];
    
    lanes.forEach(lane => {
        const lightItem = document.createElement('div');
        lightItem.className = 'traffic-light-item';
        
        const status = lane.is_green ? 'green' : 'red';
        let reason = 'Lower traffic';
        
        if (lane.is_green) {
            reason = 'Highest traffic';
        }
        
        lightItem.classList.add(status);
        
        const lightEmoji = status === 'green' ? '🟢' : '🔴';
        
        lightItem.innerHTML = `
            <div class="light-name">Lane ${lane.lane_id}</div>
            <div class="light-status">${lightEmoji}</div>
            <div class="light-info">${reason}</div>
            <div class="light-info">Vehicles: ${lane.vehicle_count}</div>
            <div class="light-info">Green Time: ${lane.green_time}s</div>
        `;
        
        lightsContainer.appendChild(lightItem);
    });
}

// Update statistics
function updateStatistics(data) {
    const statsGrid = document.getElementById('stats-grid');
    statsGrid.innerHTML = '';
    
    const lanes = data.lanes || [];
    const totalVehicles = lanes.reduce((sum, lane) => sum + lane.vehicle_count, 0);
    const greenLights = lanes.filter(lane => lane.is_green).length;
    
    const stats = [
        { label: 'Total Vehicles', value: totalVehicles },
        { label: 'Green Signals', value: greenLights },
        { label: 'Red Signals', value: 4 - greenLights },
        { label: 'Active Detections', value: lanes.reduce((sum, lane) => sum + (lane.detection_boxes?.length || 0), 0) }
    ];
    
    stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `
            <div class="stat-card-label">${stat.label}</div>
            <div class="stat-card-value">${stat.value}</div>
        `;
        statsGrid.appendChild(card);
    });
}


// Update analysis status
function updateAnalysisStatus(status) {
    document.getElementById('analysis-status').textContent = status;
}

// ============================================
// Blockchain Functions
// ============================================

let blockchainRefreshInterval = null;
let currentLaneFilter = 'all';

// Initialize blockchain UI
function initializeBlockchain() {
    // Setup event listeners
    document.getElementById('refresh-blockchain-btn')?.addEventListener('click', () => {
        loadBlockchainTransactions();
    });
    
    document.getElementById('blockchain-stats-btn')?.addEventListener('click', () => {
        toggleBlockchainStats();
    });
    
    document.getElementById('close-stats-btn')?.addEventListener('click', () => {
        document.getElementById('blockchain-stats-card').style.display = 'none';
    });
    
    document.getElementById('blockchain-lane-filter')?.addEventListener('change', (e) => {
        currentLaneFilter = e.target.value;
        loadBlockchainTransactions();
    });
    
    // Load initial data
    loadBlockchainStats();
    loadBlockchainTransactions();
    
    // Auto-refresh every 5 seconds
    if (blockchainRefreshInterval) {
        clearInterval(blockchainRefreshInterval);
    }
    blockchainRefreshInterval = setInterval(() => {
        if (analysis_running) {
            loadBlockchainStats();
            loadBlockchainTransactions();
        }
    }, 5000);
}

// Load blockchain statistics
async function loadBlockchainStats() {
    try {
        const response = await fetch('http://localhost:5000/api/blockchain/stats');
        const data = await response.json();
        
        if (data.success && data.stats) {
            const stats = data.stats;
            
            document.getElementById('bc-total-blocks').textContent = stats.total_blocks || 0;
            document.getElementById('bc-total-transactions').textContent = stats.total_transactions || 0;
            document.getElementById('bc-pending-transactions').textContent = stats.pending_transactions || 0;
            
            const statusBadge = document.getElementById('bc-status-badge');
            if (stats.is_valid) {
                statusBadge.textContent = '✓ Valid';
                statusBadge.className = 'status-badge valid';
            } else {
                statusBadge.textContent = '✗ Invalid';
                statusBadge.className = 'status-badge invalid';
            }
        }
    } catch (error) {
        console.error('Error loading blockchain stats:', error);
    }
}

// Load blockchain transactions
async function loadBlockchainTransactions() {
    const transactionsContainer = document.getElementById('blockchain-transactions');
    
    try {
        let transactions = [];
        
        if (currentLaneFilter === 'all') {
            // Get all transactions from all lanes
            const lanes = [1, 2, 3, 4];
            const promises = lanes.map(laneId => 
                fetch(`http://localhost:5000/api/blockchain/lane/${laneId}`)
                    .then(res => res.json())
                    .then(data => data.success ? data.transactions : [])
                    .catch(() => [])
            );
            
            const results = await Promise.all(promises);
            transactions = results.flat();
        } else {
            // Get transactions for specific lane
            const response = await fetch(`http://localhost:5000/api/blockchain/lane/${currentLaneFilter}`);
            const data = await response.json();
            
            if (data.success) {
                transactions = data.transactions || [];
            }
        }
        
        // Sort by timestamp (newest first)
        transactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Display transactions
        displayBlockchainTransactions(transactions);
        
    } catch (error) {
        console.error('Error loading blockchain transactions:', error);
        transactionsContainer.innerHTML = `
            <div class="blockchain-error">
                Error loading transactions: ${error.message}
            </div>
        `;
    }
}

// Display blockchain transactions
function displayBlockchainTransactions(transactions) {
    const container = document.getElementById('blockchain-transactions');
    
    if (!transactions || transactions.length === 0) {
        container.innerHTML = `
            <div class="blockchain-empty">
                No transactions found${currentLaneFilter !== 'all' ? ` for Lane ${currentLaneFilter}` : ''}
            </div>
        `;
        return;
    }
    
    // Limit to 50 most recent transactions
    const recentTransactions = transactions.slice(0, 50);
    
    container.innerHTML = recentTransactions.map(tx => {
        const timestamp = new Date(tx.timestamp).toLocaleString();
        const signalStateClass = tx.signal_state.toLowerCase();
        const emergencyBadge = tx.emergency_vehicle 
            ? '<span class="emergency-badge">🚨 Emergency</span>' 
            : '';
        
        return `
            <div class="blockchain-transaction-card">
                <div class="transaction-header">
                    <div class="transaction-lane">Lane ${tx.lane_id}</div>
                    <div class="transaction-timestamp">${timestamp}</div>
                </div>
                <div class="transaction-body">
                    <div class="transaction-signal signal-${signalStateClass}">
                        <span class="signal-icon">${getSignalIcon(tx.signal_state)}</span>
                        <span class="signal-text">${tx.signal_state}</span>
                        ${emergencyBadge}
                    </div>
                    <div class="transaction-details">
                        <div class="transaction-detail">
                            <span class="detail-label">Vehicles:</span>
                            <span class="detail-value">${tx.vehicle_count}</span>
                        </div>
                        <div class="transaction-detail">
                            <span class="detail-label">Green Time:</span>
                            <span class="detail-value">${tx.green_time}s</span>
                        </div>
                        <div class="transaction-detail">
                            <span class="detail-label">Node:</span>
                            <span class="detail-value">${tx.node_id}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Get signal icon
function getSignalIcon(state) {
    switch(state) {
        case 'GREEN': return '🟢';
        case 'RED': return '🔴';
        case 'YELLOW': return '🟡';
        default: return '⚪';
    }
}

// Toggle blockchain stats card
function toggleBlockchainStats() {
    const statsCard = document.getElementById('blockchain-stats-card');
    if (statsCard.style.display === 'none' || !statsCard.style.display) {
        statsCard.style.display = 'block';
        loadBlockchainStats();
    } else {
        statsCard.style.display = 'none';
    }
}
