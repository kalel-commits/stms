"""
Main entry point to run the full-stack traffic management system
"""
import subprocess
import sys
import os
import time

def run_backend():
    """Start the Flask backend server"""
    print("Starting backend server...")
    os.chdir('backend')
    subprocess.Popen([sys.executable, 'app.py'])
    os.chdir('..')
    time.sleep(2)
    print("✓ Backend server started on http://localhost:5000")

def run_ai_model(road_id, source_type, source_path):
    """Start AI model for a specific road"""
    print(f"Starting AI model for Road {road_id}...")
    if source_type == "camera":
        subprocess.Popen([sys.executable, 'ai_model.py', 'camera', str(road_id), source_path])
    elif source_type == "video":
        subprocess.Popen([sys.executable, 'ai_model.py', 'video', str(road_id), source_path])
    print(f"✓ AI model started for Road {road_id}")

if __name__ == "__main__":
    print("=" * 50)
    print("Smart Traffic Management System")
    print("=" * 50)
    print()
    
    # Start backend
    run_backend()
    
    print()
    print("Backend API: http://localhost:5000")
    print("Frontend: http://localhost:5000 (served by backend)")
    print()
    print("To start AI model detection, run:")
    print("  python ai_model.py camera <road_id> <camera_index>")
    print("  python ai_model.py video <road_id> <video_path>")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

