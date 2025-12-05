from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os
import threading
import time
import cv2
import numpy as np
from ultralytics import YOLO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

# Create upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state
lanes = {}  # {lane_id: {video_path, vehicle_count, green_time, video_url}}
analysis_running = False
analysis_thread = None

# Initialize YOLO model
model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "yolo11n.pt")
if os.path.exists(model_path):
    model = YOLO(model_path)
else:
    print(f"Warning: Model file not found at {model_path}, using default YOLO model")
    model = YOLO('yolo11n.pt')

# Vehicle classes in COCO dataset
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
# We'll detect by visual features and class name matching

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_video(video_path, lane_id):
    """Analyze video for vehicle count"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return 0
    
    total_vehicles = 0
    frame_count = 0
    sample_frames = []
    
    # Sample frames from video (every 30 frames)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        if frame_count % 30 == 0:
            sample_frames.append(frame)
    
    cap.release()
    
    if not sample_frames:
        # If no frames sampled, try to get at least one frame
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        if ret:
            sample_frames = [frame]
        cap.release()
    
    # Analyze sampled frames using YOLO
    for frame in sample_frames:
        try:
            # Run YOLO detection
            results = model(frame, verbose=False, conf=0.3)
            
            vehicle_count_frame = 0
            
            # Process detections
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        # Get class name
                        class_name = model.names[cls].lower()
                        
                        # Check for vehicles
                        if cls in VEHICLE_CLASSES or any(v in class_name for v in ['car', 'bus', 'truck', 'motorcycle', 'bike']):
                            vehicle_count_frame += 1
            
            total_vehicles += vehicle_count_frame
            
        except Exception as e:
            print(f"Error analyzing frame: {e}")
            continue
    
    # Average vehicle count
    avg_vehicles = total_vehicles // len(sample_frames) if sample_frames else 0
    
    return avg_vehicles

def calculate_green_time(vehicle_count, base_time=30, max_time=90):
    """Calculate green time based on vehicle count"""
    # More vehicles = longer green time
    # Formula: base_time + (vehicle_count * multiplier)
    multiplier = 1.5
    green_time = base_time + (vehicle_count * multiplier)
    
    return min(int(green_time), max_time)

def determine_traffic_lights():
    """Determine which lanes should be green/red - ONLY ONE LANE GREEN AT A TIME"""
    global lanes
    
    # First, set ALL lanes to RED
    for lane_id in lanes:
        lanes[lane_id]['is_green'] = False
    
    # Find lane with highest traffic
    if not lanes:
        return
    
    # Find lane with highest traffic
    max_traffic = max((data.get('vehicle_count', 0) for data in lanes.values()), default=0)
    
    if max_traffic == 0:
        # If no traffic, default to Lane 1
        if 1 in lanes:
            lanes[1]['is_green'] = True
        return
    
    # Find the FIRST lane with highest traffic (in case of ties, pick the first one)
    highest_traffic_lane = None
    for lane_id in sorted(lanes.keys()):  # Sort to ensure consistent selection
        if lanes[lane_id].get('vehicle_count', 0) == max_traffic:
            highest_traffic_lane = lane_id
            break
    
    # Set green for ONLY the highest traffic lane
    if highest_traffic_lane:
        lanes[highest_traffic_lane]['is_green'] = True
        print(f"Traffic priority: Lane {highest_traffic_lane} (vehicles: {max_traffic}) set to GREEN")

def analysis_worker():
    """Background worker to continuously analyze videos"""
    global lanes, analysis_running
    
    while analysis_running:
        try:
            updated_lanes = []
            
            for lane_id, lane_data in lanes.items():
                video_path = lane_data.get('video_path')
                if not video_path or not os.path.exists(video_path):
                    continue
                
                # Analyze video
                vehicle_count = analyze_video(video_path, lane_id)
                
                # Calculate green time
                green_time = calculate_green_time(vehicle_count)
                
                # Update lane data
                lanes[lane_id]['vehicle_count'] = vehicle_count
                lanes[lane_id]['green_time'] = green_time
                
                updated_lanes.append({
                    'lane_id': lane_id,
                    'vehicle_count': vehicle_count,
                    'green_time': green_time,
                    'video_url': lane_data.get('video_url', ''),
                    'is_green': lanes[lane_id].get('is_green', False)
                })
            
            # Determine traffic lights
            determine_traffic_lights()
            
            # Add is_green status to updated lanes
            for lane in updated_lanes:
                lane['is_green'] = lanes[lane['lane_id']].get('is_green', False)
            
            # Emit update to frontend
            socketio.emit('analysis_update', {
                'status': 'running',
                'lanes': updated_lanes
            })
            
            time.sleep(2)  # Update every 2 seconds
            
        except Exception as e:
            print(f"Error in analysis worker: {e}")
            time.sleep(2)

# API Routes
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    """Handle video upload"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file'}), 400
        
        file = request.files['video']
        lane_id = request.form.get('lane_id')
        
        if not lane_id:
            return jsonify({'error': 'No lane_id provided'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Save file
            filename = f"lane_{lane_id}_{int(time.time())}.mp4"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Store lane data
            lanes[int(lane_id)] = {
                'video_path': filepath,
                'video_url': f'/uploads/{filename}',
                'vehicle_count': 0,
                'green_time': 30,
                'is_green': False
            }
            
            print(f"Video uploaded for Lane {lane_id}: {filename}")
            
            return jsonify({
                'success': True,
                'lane_id': int(lane_id),
                'video_url': f'/uploads/{filename}'
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded videos"""
    upload_path = os.path.join(os.path.dirname(__file__), UPLOAD_FOLDER)
    return send_from_directory(upload_path, filename)

@app.route('/api/remove-video/<int:lane_id>', methods=['DELETE'])
def remove_video(lane_id):
    """Remove uploaded video for a lane"""
    try:
        if lane_id in lanes:
            lane_data = lanes[lane_id]
            video_path = lane_data.get('video_path')
            
            # Delete video file if it exists
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print(f"Deleted video file: {video_path}")
                except Exception as e:
                    print(f"Error deleting video file: {e}")
            
            # Remove from lanes dictionary
            del lanes[lane_id]
            
            # If analysis is running and this lane was being analyzed, stop analysis for this lane
            # (The analysis worker will skip lanes that don't exist)
            
            return jsonify({
                'success': True,
                'message': f'Video for Lane {lane_id} removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No video found for Lane {lane_id}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    """Start video analysis"""
    global analysis_running, analysis_thread, lanes
    
    if len(lanes) < 4:
        return jsonify({'error': 'Please upload 4 videos first'}), 400
    
    if not analysis_running:
        analysis_running = True
        analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
        analysis_thread.start()
        
        # Initial analysis
        time.sleep(1)
        determine_traffic_lights()
        
        return jsonify({'success': True, 'message': 'Analysis started'})
    
    return jsonify({'success': True, 'message': 'Analysis already running'})

@app.route('/api/stop-analysis', methods=['POST'])
def stop_analysis():
    """Stop video analysis"""
    global analysis_running
    analysis_running = False
    return jsonify({'success': True, 'message': 'Analysis stopped'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current analysis status"""
    lanes_data = []
    for lane_id, lane_data in lanes.items():
        lanes_data.append({
            'lane_id': lane_id,
            'vehicle_count': lane_data.get('vehicle_count', 0),
            'green_time': lane_data.get('green_time', 30),
            'is_green': lane_data.get('is_green', False),
            'video_url': lane_data.get('video_url', '')
        })
    
    return jsonify({
        'analysis_running': analysis_running,
        'lanes': lanes_data
    })

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to traffic management system'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("=" * 50)
    print("Smart Traffic Management System - Backend")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    print("Upload 4 videos and start analysis!")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
