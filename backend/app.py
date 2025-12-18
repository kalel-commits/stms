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
from werkzeug.utils import secure_filename
import torch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import blockchain module
from blockchain import Blockchain, Transaction

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

# Create upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global state
lanes = {}  # {lane_id: {video_path, vehicle_count, green_time, video_url, current_frame}}
video_caps = {}  # {lane_id: VideoCapture object} - keep video streams open
frame_skip_counters = {}  # {lane_id: counter} - track frames to skip for performance
vehicle_count_history = {}  # {lane_id: [count1, count2, ...]} - for temporal smoothing
analysis_running = False
analysis_thread = None
state_lock = threading.Lock()
system_logs = []  # Store system logs
MAX_LOGS = 100  # Maximum number of logs to keep
FRAME_SKIP = 1  # Process every frame for maximum accuracy (higher compute cost)
HISTORY_SIZE = 3  # Number of recent detections to average for stability

# Initialize Blockchain for secure traffic signal management
blockchain = Blockchain(node_id="traffic_signal_node_1", difficulty=2, block_size=5)
previous_signal_states = {}  # Track previous states to avoid duplicate transactions

# Initialize YOLO model
model_path = os.path.join(PROJECT_ROOT, "yolo11n.pt")
if os.path.exists(model_path):
    model = YOLO(model_path)
else:
    print(f"Warning: Model file not found at {model_path}, using default YOLO model")
    model = YOLO('yolo11n.pt')

# Prefer GPU if available (override with env var YOLO_DEVICE, e.g. "cpu", "cuda", "0")
YOLO_DEVICE = os.environ.get("YOLO_DEVICE")
if YOLO_DEVICE is None:
    YOLO_DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"YOLO device: {YOLO_DEVICE} (cuda_available={torch.cuda.is_available()})")

# Vehicle classes in COCO dataset - expanded for better detection
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck
VEHICLE_KEYWORDS = ['car', 'bus', 'truck', 'motorcycle', 'bike', 'bicycle', 'vehicle', 'auto', 'van', 'suv']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_system_log(level, message):
    """Add a system log entry"""
    global system_logs
    import datetime
    log_entry = {
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
        'level': level,
        'message': message
    }
    system_logs.append(log_entry)
    
    # Keep only last MAX_LOGS entries
    if len(system_logs) > MAX_LOGS:
        system_logs = system_logs[-MAX_LOGS:]
    
    # Emit log via WebSocket
    socketio.emit('system_log', log_entry)

def analyze_video_frame(cap, lane_id):
    """Analyze a single frame from video for real-time detection - optimized for performance"""
    global frame_skip_counters, FRAME_SKIP, vehicle_count_history, HISTORY_SIZE
    
    if not cap or not cap.isOpened():
        return 0, []
    
    # Initialize frame skip counter for this lane
    if lane_id not in frame_skip_counters:
        frame_skip_counters[lane_id] = 0
    
    frame_skip_counters[lane_id] += 1
    
    # Read frame first (always advance video)
    ret, frame = cap.read()
    if not ret:
        # Video ended, reset to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if not ret:
            return 0, []
    
    # Skip frames for better performance (only process every Nth frame)
    if frame_skip_counters[lane_id] < FRAME_SKIP:
        # Skip processing this frame, return previous results if available
        return lanes.get(lane_id, {}).get('vehicle_count', 0), lanes.get(lane_id, {}).get('detection_boxes', [])
    
    # Reset counter - we're processing this frame
    frame_skip_counters[lane_id] = 0
    
    try:
        # Resize frame for YOLO inference - use larger size for better accuracy
        original_height, original_width = frame.shape[:2]
        # Use 832px for better accuracy (YOLO works well with multiples of 32)
        max_size = 832
        if original_width > max_size or original_height > max_size:
            # Maintain aspect ratio
            scale = min(max_size / original_width, max_size / original_height)
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            # Round to nearest multiple of 32 for optimal YOLO performance
            new_width = (new_width // 32) * 32
            new_height = (new_height // 32) * 32
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        else:
            new_width, new_height = original_width, original_height
        
        # Run YOLO detection with lower confidence threshold and better settings for accuracy
        results = model(
            frame,
            verbose=False,
            conf=0.25,
            iou=0.45,
            imgsz=max_size,
            agnostic_nms=False,
            device=YOLO_DEVICE
        )
        
        vehicle_count = 0
        detection_boxes = []
        
        # Scale factors to convert back to original frame size
        scale_x = original_width / new_width
        scale_y = original_height / new_height
        
        # Process detections
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Get class name
                    class_name = model.names[cls].lower()
                    
                    # Check for vehicles with improved matching
                    is_vehicle = (cls in VEHICLE_CLASSES) or any(keyword in class_name for keyword in VEHICLE_KEYWORDS)
                    
                    # Additional check: ensure confidence is reasonable
                    if is_vehicle and conf >= 0.25:
                        vehicle_count += 1
                        
                        # Get bounding box coordinates (from resized frame)
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Scale back to original frame size
                        x1 = x1 * scale_x
                        y1 = y1 * scale_y
                        x2 = x2 * scale_x
                        y2 = y2 * scale_y
                        
                        # Convert to percentages for frontend
                        detection_boxes.append({
                            'x': float(x1 / original_width * 100),  # Percentage of width
                            'y': float(y1 / original_height * 100),  # Percentage of height
                            'width': float((x2 - x1) / original_width * 100),
                            'height': float((y2 - y1) / original_height * 100),
                            'class': class_name,
                            'confidence': float(conf)
                        })
        
        # Apply temporal smoothing for vehicle count (average recent detections)
        if lane_id not in vehicle_count_history:
            vehicle_count_history[lane_id] = []
        
        vehicle_count_history[lane_id].append(vehicle_count)
        if len(vehicle_count_history[lane_id]) > HISTORY_SIZE:
            vehicle_count_history[lane_id].pop(0)
        
        # Use average of recent counts for stability
        smoothed_count = int(sum(vehicle_count_history[lane_id]) / len(vehicle_count_history[lane_id]))
        
        return smoothed_count, detection_boxes
        
    except Exception as e:
        print(f"Error analyzing frame for lane {lane_id}: {e}")
        return 0, []

def calculate_green_time(vehicle_count, base_time=30, max_time=90):
    """Calculate green time based on vehicle count"""
    # More vehicles = longer green time
    # Formula: base_time + (vehicle_count * multiplier)
    multiplier = 1.5
    green_time = base_time + (vehicle_count * multiplier)
    
    return min(int(green_time), max_time)

def record_blockchain_transaction(lane_id, signal_state, vehicle_count, green_time, emergency_vehicle=False):
    """
    Record a traffic signal state change in the blockchain
    
    Args:
        lane_id: ID of the lane
        signal_state: Current signal state ('GREEN', 'RED', 'YELLOW')
        vehicle_count: Number of vehicles detected
        green_time: Calculated green light duration
        emergency_vehicle: Whether emergency vehicle is present
    """
    global blockchain, previous_signal_states
    
    # Check if state has changed to avoid duplicate transactions
    state_key = f"lane_{lane_id}"
    current_state = {
        'signal_state': signal_state,
        'vehicle_count': vehicle_count,
        'emergency_vehicle': emergency_vehicle
    }
    
    # Only record if state has changed
    if state_key in previous_signal_states:
        prev_state = previous_signal_states[state_key]
        if (prev_state['signal_state'] == signal_state and 
            prev_state['vehicle_count'] == vehicle_count and
            prev_state['emergency_vehicle'] == emergency_vehicle):
            return  # No change, skip transaction
    
    # Create and add transaction to blockchain
    transaction = Transaction(
        lane_id=lane_id,
        signal_state=signal_state,
        vehicle_count=vehicle_count,
        green_time=green_time,
        emergency_vehicle=emergency_vehicle,
        node_id=blockchain.node_id,
        metadata={'green_time': green_time}
    )
    
    if blockchain.add_transaction(transaction):
        previous_signal_states[state_key] = current_state
        add_system_log('info', f'Blockchain: Recorded {signal_state} state for Lane {lane_id}')
        
        # Emit blockchain update via WebSocket
        socketio.emit('blockchain_transaction', {
            'type': 'transaction',
            'transaction': transaction.to_dict(),
            'stats': blockchain.get_statistics()
        })
    
    # Mine block if pending transactions reach threshold
    if len(blockchain.pending_transactions) >= blockchain.block_size:
        mined_block = blockchain.mine_pending_transactions()
        if mined_block:
            add_system_log('success', f'Blockchain: Mined block #{mined_block.index} with {len(mined_block.transactions)} transactions')
            
            # Emit block mined event via WebSocket
            socketio.emit('blockchain_block_mined', {
                'type': 'block_mined',
                'block': mined_block.to_dict(),
                'stats': blockchain.get_statistics()
            })

def determine_traffic_lights():
    """Determine which lanes should be green/red - ONLY ONE LANE GREEN AT A TIME"""
    global lanes
    
    # First, set ALL lanes to RED and record in blockchain
    for lane_id in lanes:
        if lanes[lane_id].get('is_green', False):  # Only record if state changed
            lane_data = lanes[lane_id]
            record_blockchain_transaction(
                lane_id=lane_id,
                signal_state='RED',
                vehicle_count=lane_data.get('vehicle_count', 0),
                green_time=lane_data.get('green_time', 30),
                emergency_vehicle=False
            )
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
            record_blockchain_transaction(
                lane_id=1,
                signal_state='GREEN',
                vehicle_count=lanes[1].get('vehicle_count', 0),
                green_time=lanes[1].get('green_time', 30),
                emergency_vehicle=False
            )
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
        lane_data = lanes[highest_traffic_lane]
        
        # Record state change in blockchain
        record_blockchain_transaction(
            lane_id=highest_traffic_lane,
            signal_state='GREEN',
            vehicle_count=lane_data.get('vehicle_count', 0),
            green_time=lane_data.get('green_time', 30),
            emergency_vehicle=lane_data.get('emergency_vehicle', False)
        )
        
        add_system_log('success', f'Lane {highest_traffic_lane} set to GREEN (vehicles: {max_traffic})')
        print(f"Traffic priority: Lane {highest_traffic_lane} (vehicles: {max_traffic}) set to GREEN")

def analysis_worker():
    """Background worker to continuously analyze videos frame by frame for real-time detection"""
    global lanes, analysis_running, video_caps
    
    while analysis_running:
        try:
            updated_lanes = []

            with state_lock:
                lanes_snapshot = list(lanes.items())

            for lane_id, lane_data in lanes_snapshot:
                video_path = lane_data.get('video_path')
                if not video_path or not os.path.exists(video_path):
                    continue
                
                # Initialize or get video capture for this lane
                if lane_id not in video_caps:
                    cap = cv2.VideoCapture(video_path)
                    if cap.isOpened():
                        video_caps[lane_id] = cap
                    else:
                        continue
                else:
                    cap = video_caps[lane_id]
                
                # Analyze current frame (real-time detection)
                vehicle_count, detection_boxes = analyze_video_frame(cap, lane_id)
                
                # Calculate green time
                green_time = calculate_green_time(vehicle_count)
                
                # Update lane data
                with state_lock:
                    if lane_id in lanes:
                        lanes[lane_id]['vehicle_count'] = vehicle_count
                        lanes[lane_id]['green_time'] = green_time
                        lanes[lane_id]['detection_boxes'] = detection_boxes
                
                updated_lanes.append({
                    'lane_id': lane_id,
                    'vehicle_count': vehicle_count,
                    'green_time': green_time,
                    'video_url': lane_data.get('video_url', ''),
                    'is_green': lanes[lane_id].get('is_green', False),
                    'detection_boxes': detection_boxes
                })
            
            # Determine traffic lights
            with state_lock:
                determine_traffic_lights()
            
            # Add is_green status to updated lanes
            for lane in updated_lanes:
                with state_lock:
                    lane['is_green'] = lanes.get(lane['lane_id'], {}).get('is_green', False)
                
            # Log traffic switch if it happened
            green_lanes = [lid for lid, data in lanes.items() if data.get('is_green', False)]
            if green_lanes:
                add_system_log('info', f'Traffic signal: Lane {green_lanes[0]} is GREEN')
            
            # Emit update to frontend
            socketio.emit('analysis_update', {
                'status': 'running',
                'lanes': updated_lanes
            })
            
            # Emit traffic update for charts
            traffic_data = {
                'timestamp': time.time(),
                'lanes': {lid: data.get('vehicle_count', 0) for lid, data in lanes.items()}
            }
            socketio.emit('traffic_data', traffic_data)
            
            time.sleep(1.5)  # Update every 1.5 seconds to reduce CPU load
            
        except Exception as e:
            print(f"Error in analysis worker: {e}")
            time.sleep(1.5)
    
    # Clean up video captures when analysis stops
    for cap in video_caps.values():
        if cap:
            cap.release()
    video_caps.clear()
    frame_skip_counters.clear()
    vehicle_count_history.clear()

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

        try:
            lane_id_int = int(lane_id)
        except ValueError:
            return jsonify({'error': 'lane_id must be an integer'}), 400

        if lane_id_int not in (1, 2, 3, 4):
            return jsonify({'error': 'lane_id must be between 1 and 4'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Save file (always store as .mp4 to keep frontend simple, but sanitize name anyway)
            _original = secure_filename(file.filename or "")
            filename = f"lane_{lane_id}_{int(time.time())}.mp4"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Store lane data
            with state_lock:
                lanes[lane_id_int] = {
                'video_path': filepath,
                'video_url': f'/uploads/{filename}',
                'vehicle_count': 0,
                'green_time': 30,
                'is_green': False
                }
            
            print(f"Video uploaded for Lane {lane_id}: {filename}")
            
            return jsonify({
                'success': True,
                'lane_id': lane_id_int,
                'video_url': f'/uploads/{filename}'
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded videos"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/remove-video/<int:lane_id>', methods=['DELETE'])
def remove_video(lane_id):
    """Remove uploaded video for a lane"""
    global video_caps, frame_skip_counters, vehicle_count_history
    try:
        with state_lock:
            lane_data = lanes.get(lane_id)

        if lane_data:
            video_path = lane_data.get('video_path')
            
            # Clean up video capture if exists
            if lane_id in video_caps:
                cap = video_caps[lane_id]
                if cap:
                    cap.release()
                del video_caps[lane_id]
            
            # Clean up frame skip counter
            if lane_id in frame_skip_counters:
                del frame_skip_counters[lane_id]
            
            # Clean up vehicle count history
            if lane_id in vehicle_count_history:
                del vehicle_count_history[lane_id]
            
            # Delete video file if it exists
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print(f"Deleted video file: {video_path}")
                except Exception as e:
                    print(f"Error deleting video file: {e}")
            
            # Remove from lanes dictionary
            with state_lock:
                if lane_id in lanes:
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
    
    with state_lock:
        lane_count = len(lanes)

    if lane_count < 4:
        return jsonify({'error': 'Please upload 4 videos first'}), 400
    
    if not analysis_running:
        analysis_running = True
        add_system_log('info', 'Starting video analysis for all lanes')
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
    add_system_log('info', 'Analysis stopped')

    # Emit stopped status to frontend (best-effort)
    with state_lock:
        lanes_data = [
            {
                'lane_id': lane_id,
                'vehicle_count': lane_data.get('vehicle_count', 0),
                'green_time': lane_data.get('green_time', 30),
                'is_green': lane_data.get('is_green', False),
                'video_url': lane_data.get('video_url', ''),
                'detection_boxes': lane_data.get('detection_boxes', [])
            }
            for lane_id, lane_data in lanes.items()
        ]
    socketio.emit('analysis_update', {'status': 'stopped', 'lanes': lanes_data})
    return jsonify({'success': True, 'message': 'Analysis stopped'})

@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Stop analysis and clear uploaded videos + state."""
    global analysis_running, lanes, video_caps, frame_skip_counters, vehicle_count_history
    analysis_running = False

    # Release captures
    for cap in list(video_caps.values()):
        try:
            if cap:
                cap.release()
        except Exception:
            pass
    video_caps.clear()
    frame_skip_counters.clear()
    vehicle_count_history.clear()

    # Delete uploaded files + clear lanes
    with state_lock:
        lane_items = list(lanes.items())
        lanes.clear()

    deleted = 0
    for _, lane_data in lane_items:
        video_path = lane_data.get('video_path')
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                deleted += 1
            except Exception:
                pass

    add_system_log('info', f'System reset: cleared {len(lane_items)} lanes, deleted {deleted} files')
    socketio.emit('analysis_update', {'status': 'reset', 'lanes': []})
    return jsonify({'success': True, 'message': 'System reset', 'cleared_lanes': len(lane_items), 'deleted_files': deleted})

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
            'video_url': lane_data.get('video_url', ''),
            'detection_boxes': lane_data.get('detection_boxes', [])
        })
    
    return jsonify({
        'analysis_running': analysis_running,
        'lanes': lanes_data
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get system logs"""
    return jsonify({'logs': system_logs[-50:]})  # Return last 50 logs

# Blockchain API Routes
@app.route('/api/blockchain/stats', methods=['GET'])
def get_blockchain_stats():
    """Get blockchain statistics"""
    try:
        stats = blockchain.get_statistics()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/chain', methods=['GET'])
def get_blockchain():
    """Get the full blockchain"""
    try:
        chain_data = blockchain.to_dict()
        return jsonify({'success': True, 'blockchain': chain_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/validate', methods=['GET'])
def validate_blockchain():
    """Validate blockchain integrity"""
    try:
        is_valid = blockchain.is_chain_valid()
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'chain_length': len(blockchain.chain)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/lane/<int:lane_id>', methods=['GET'])
def get_lane_transactions(lane_id):
    """Get all transactions for a specific lane"""
    try:
        transactions = blockchain.get_transactions_by_lane(lane_id)
        transactions_data = [tx.to_dict() for tx in transactions]
        return jsonify({
            'success': True,
            'lane_id': lane_id,
            'transaction_count': len(transactions_data),
            'transactions': transactions_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/lane/<int:lane_id>/latest', methods=['GET'])
def get_latest_lane_state(lane_id):
    """Get the latest signal state for a specific lane"""
    try:
        latest_tx = blockchain.get_latest_signal_state(lane_id)
        if latest_tx:
            return jsonify({
                'success': True,
                'lane_id': lane_id,
                'transaction': latest_tx.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'lane_id': lane_id,
                'transaction': None,
                'message': 'No transactions found for this lane'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/block/<int:block_index>', methods=['GET'])
def get_block(block_index):
    """Get a specific block by index"""
    try:
        if block_index < 0 or block_index >= len(blockchain.chain):
            return jsonify({
                'success': False,
                'error': f'Block index {block_index} out of range. Chain length: {len(blockchain.chain)}'
            }), 404
        
        block = blockchain.chain[block_index]
        return jsonify({
            'success': True,
            'block': block.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/mine', methods=['POST'])
def mine_pending_transactions():
    """Manually trigger mining of pending transactions"""
    try:
        if not blockchain.pending_transactions:
            return jsonify({
                'success': True,
                'message': 'No pending transactions to mine'
            })
        
        mined_block = blockchain.mine_pending_transactions()
        if mined_block:
            add_system_log('success', f'Blockchain: Manually mined block #{mined_block.index}')
            return jsonify({
                'success': True,
                'message': f'Block #{mined_block.index} mined successfully',
                'block': mined_block.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to mine block'
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    print(f"Blockchain initialized: Node ID = {blockchain.node_id}")
    print(f"Blockchain stats: {len(blockchain.chain)} blocks, {len(blockchain.pending_transactions)} pending transactions")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
