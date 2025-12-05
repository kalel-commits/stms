"""
AI Model for Vehicle Detection
This module processes video/camera feeds and sends data to the backend API
"""
import cv2
from ultralytics import solutions
import requests
import time
import json

# API endpoint
API_URL = "http://localhost:5000/api/ai/update"

# Define region points for detection
region_points = [(20, 400), (1080, 404), (1080, 360), (20, 360), (20, 400)]

# Initialize Object Counter with specified region and model
counter = solutions.ObjectCounter(
    show=False,  # Set to True to see detection window
    region=region_points,
    model="yolo11n.pt",
)

# Road to camera mapping (you can configure this)
road_camera_map = {
    1: 0,  # Road 1 -> Camera 0
    2: 0,  # Road 2 -> Camera 0 (or different camera)
    3: 0,
    4: 0,
    5: 0,
    6: 0,
}

def detect_vehicles_from_camera(camera_index, road_id):
    """
    Detect vehicles from camera feed and send to backend
    
    Args:
        camera_index: Camera device index or video file path
        road_id: ID of the road this camera is monitoring
    """
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return
    
    frame_count = 0
    update_interval = 30  # Update backend every 30 frames
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Could not read frame")
                break
            
            frame_count += 1
            
            # Process every Nth frame
            if frame_count % update_interval == 0:
                # Detect vehicles in the frame
                result = counter.count(frame)
                detections = result.get("detections", [])
                
                # Calculate vehicle count and check for emergency vehicles
                vehicle_count = sum(1 for d in detections if d.get("class") in ["bike", "car", "bus", "truck"])
                has_emergency_vehicle = any(d.get("class") in ["cops", "ambulance", "fire truck"] for d in detections)
                
                # Send data to backend
                send_to_backend(road_id, vehicle_count, has_emergency_vehicle)
                
                print(f"Road {road_id}: {vehicle_count} vehicles, Emergency: {has_emergency_vehicle}")
            
            # Optional: Display frame (uncomment if needed)
            # cv2.imshow('Vehicle Detection', frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            
    except KeyboardInterrupt:
        print("Stopping detection...")
    finally:
        cap.release()
        cv2.destroyAllWindows()

def detect_vehicles_from_video(video_path, road_id):
    """
    Detect vehicles from video file and send to backend
    
    Args:
        video_path: Path to video file
        road_id: ID of the road this video represents
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return
    
    frame_count = 0
    update_interval = 30  # Update backend every 30 frames
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_count += 1
            
            # Process every Nth frame
            if frame_count % update_interval == 0:
                # Detect vehicles in the frame
                result = counter.count(frame)
                detections = result.get("detections", [])
                
                # Calculate vehicle count and check for emergency vehicles
                vehicle_count = sum(1 for d in detections if d.get("class") in ["bike", "car", "bus", "truck"])
                has_emergency_vehicle = any(d.get("class") in ["cops", "ambulance", "fire truck"] for d in detections)
                
                # Send data to backend
                send_to_backend(road_id, vehicle_count, has_emergency_vehicle)
                
                print(f"Road {road_id}: {vehicle_count} vehicles, Emergency: {has_emergency_vehicle}")
            
            time.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("Stopping detection...")
    finally:
        cap.release()

def send_to_backend(road_id, vehicle_count, has_emergency):
    """
    Send detection data to backend API
    
    Args:
        road_id: ID of the road
        vehicle_count: Number of vehicles detected
        has_emergency: Boolean indicating emergency vehicle presence
    """
    try:
        payload = {
            "road_id": road_id,
            "vehicle_count": vehicle_count,
            "has_emergency": has_emergency
        }
        
        response = requests.post(API_URL, json=payload, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ Data sent to backend for Road {road_id}")
        else:
            print(f"✗ Error sending data: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection error: {e}")

def process_single_image(image_path, road_id):
    """
    Process a single image and send results to backend
    
    Args:
        image_path: Path to image file
        road_id: ID of the road
    """
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Could not read image {image_path}")
        return
    
    # Detect vehicles
    result = counter.count(image)
    detections = result.get("detections", [])
    
    # Calculate vehicle count and check for emergency vehicles
    vehicle_count = sum(1 for d in detections if d.get("class") in ["bike", "car", "bus", "truck"])
    has_emergency_vehicle = any(d.get("class") in ["cops", "ambulance", "fire truck"] for d in detections)
    
    # Send data to backend
    send_to_backend(road_id, vehicle_count, has_emergency_vehicle)
    
    print(f"Road {road_id}: {vehicle_count} vehicles, Emergency: {has_emergency_vehicle}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python ai_model.py camera <road_id> <camera_index>")
        print("  python ai_model.py video <road_id> <video_path>")
        print("  python ai_model.py image <road_id> <image_path>")
        sys.exit(1)
    
    mode = sys.argv[1]
    road_id = int(sys.argv[2])
    
    if mode == "camera":
        camera_index = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        detect_vehicles_from_camera(camera_index, road_id)
    elif mode == "video":
        video_path = sys.argv[3]
        detect_vehicles_from_video(video_path, road_id)
    elif mode == "image":
        image_path = sys.argv[3]
        process_single_image(image_path, road_id)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

