// State
let videos = {};
let analysisResults = {};
let socket = null;
let analysisInterval = null;
let analysis_running = false;
let emergencyNotified = {};  // Track which lanes have already shown emergency alerts

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupVideoUploads();
    setupAnalyzeButton();
    connectWebSocket();
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
                    has_emergency: false,
                    green_time: 30,
                    is_green: false
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
    
    socket.on('emergency_detected', (data) => {
        handleEmergencyDetected(data);
    });
}

// Update analysis results
function updateAnalysisResults(data) {
    analysisResults = data;
    
    // Update status
    if (data.status === 'complete') {
        updateAnalysisStatus('Analysis Complete');
    }
    
    // Clear emergency notifications for lanes that no longer have emergency
    if (data.lanes) {
        const lanesWithEmergency = data.lanes.filter(lane => lane.has_emergency).map(lane => lane.lane_id);
        for (const laneId in emergencyNotified) {
            if (!lanesWithEmergency.includes(parseInt(laneId))) {
                delete emergencyNotified[laneId];
            }
        }
    }
    
    // Update video grid
    updateVideoGrid(data.lanes);
    
    // Update statistics
    updateStatistics(data);
    
    // Update traffic lights
    updateTrafficLights(data);
}

// Update video grid
function updateVideoGrid(lanes) {
    const grid = document.getElementById('video-grid');
    grid.innerHTML = '';
    
    // Check for emergency vehicles first (highest priority)
    const emergencyLanes = lanes.filter(lane => lane.has_emergency);
    
    // Find highest traffic lane (only if no emergency)
    let maxTraffic = 0;
    let highestLane = null;
    
    if (emergencyLanes.length === 0) {
        lanes.forEach(lane => {
            if (lane.vehicle_count > maxTraffic) {
                maxTraffic = lane.vehicle_count;
                highestLane = lane.lane_id;
            }
        });
    }
    
    lanes.forEach(lane => {
        const card = document.createElement('div');
        card.className = 'video-analysis-card';
        
        // Determine light status based on backend decision
        const isGreen = lane.is_green;
        
        // Add classes based on state
        if (lane.has_emergency) {
            card.classList.add('emergency', 'green-light');
        } else if (isGreen) {
            card.classList.add('highest-traffic', 'green-light');
        } else {
            card.classList.add('red-light');
        }
        
        const lightStatus = lane.is_green ? 'green' : 'red';
        const lightEmoji = lightStatus === 'green' ? '🟢' : '🔴';
        
        card.innerHTML = `
            <div class="video-header">
                <span class="video-title">Lane ${lane.lane_id}</span>
                <div class="traffic-light-indicator ${lightStatus}">${lightEmoji}</div>
            </div>
            <div class="video-container">
                <video src="http://localhost:5000${lane.video_url}" controls autoplay loop muted></video>
                <div class="video-overlay">
                    <div>Vehicles: ${lane.vehicle_count}</div>
                    ${lane.has_emergency ? '<div style="color: #f44336; font-weight: bold;">🚨 Emergency Vehicle Detected!</div>' : ''}
                </div>
            </div>
            <div class="video-stats">
                <div class="stat-box">
                    <div class="stat-label">Vehicle Count</div>
                    <div class="stat-value vehicles">${lane.vehicle_count}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Emergency</div>
                    <div class="stat-value emergency">${lane.has_emergency ? '🚨 YES' : 'No'}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Signal Status</div>
                    <div class="stat-value" style="color: ${lightStatus === 'green' ? '#4CAF50' : '#f44336'};">
                        ${lightStatus.toUpperCase()}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Green Time</div>
                    <div class="stat-value" style="color: #667eea;">${lane.green_time}s</div>
                </div>
            </div>
        `;
        
        grid.appendChild(card);
    });
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
        
        if (lane.has_emergency) {
            reason = '🚨 Emergency Vehicle';
            lightItem.classList.add('emergency');
        } else if (lane.is_green) {
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
    const emergencyCount = lanes.filter(lane => lane.has_emergency).length;
    const greenLights = lanes.filter(lane => 
        lane.has_emergency || lane.lane_id === lanes.reduce((max, l) => 
            l.vehicle_count > (lanes.find(l2 => l2.lane_id === max)?.vehicle_count || 0) ? l.lane_id : max, lanes[0]?.lane_id)
    ).length;
    
    const stats = [
        { label: 'Total Vehicles', value: totalVehicles },
        { label: 'Emergency Vehicles', value: emergencyCount },
        { label: 'Green Signals', value: greenLights },
        { label: 'Red Signals', value: 4 - greenLights }
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

// Handle emergency detection
function handleEmergencyDetected(data) {
    const laneId = data.lane_id;
    
    // Only show alert if this is a new emergency (not already notified)
    if (!emergencyNotified[laneId]) {
        const emergencyStatus = document.getElementById('emergency-status');
        const noEmergency = document.getElementById('no-emergency');
        
        emergencyStatus.style.display = 'inline-block';
        noEmergency.style.display = 'none';
        
        // Show alert only once
        alert(`🚨 Emergency vehicle detected on Lane ${laneId}! Signal switched to green.`);
        
        // Mark as notified
        emergencyNotified[laneId] = true;
        
        // Update display
        updateTrafficLights(analysisResults);
    }
}

// Update analysis status
function updateAnalysisStatus(status) {
    document.getElementById('analysis-status').textContent = status;
}
