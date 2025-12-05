# Quick Setup Guide

## ✅ Project Setup Complete!

This Smart Traffic Management System is now ready to run.

## 📋 Features

- ✅ **Real-Time Traffic Control**: Dynamically adjusts traffic light timings
- ✅ **Emergency Vehicle Prioritization**: Detects and prioritizes emergency vehicles
- ✅ **Adaptive Timing**: Calculates optimal green-light durations based on vehicle density
- ✅ **SQLite Database**: Stores traffic data for analysis

## 🚀 How to Run

1. **Navigate to the project directory:**
   ```bash
   cd Smart-Adaptive-Traffic-Management-System
   ```

2. **Run the main program:**
   ```bash
   python main.py
   ```

## 📁 Project Structure

- `main.py` - Main control loop for traffic management
- `road.py` - Road class with traffic logic
- `detection.py` - Vehicle detection using YOLO
- `database.py` - SQLite database operations
- `yolo11n.pt` - YOLO model weights
- `road.db` - SQLite database (created automatically)

## 🎯 How It Works

1. **Initialization**: Creates 4 roads in a circular network
2. **Traffic Monitoring**: Updates vehicle counts every second
3. **Signal Control**: Switches green lights based on calculated timing
4. **Emergency Detection**: Automatically prioritizes roads with emergency vehicles
5. **Dynamic Timing**: Adjusts green time based on vehicle density

## 📊 System Behavior

- Vehicle counts update every 1 second
- Green light switches automatically based on calculated timing
- Emergency vehicles trigger immediate priority (5-second duration)
- Green time = (vehicle_count / capacity) × total_time

## 🔧 Dependencies

All dependencies are already installed:
- ultralytics (YOLO)
- opencv-python
- numpy
- sqlite3 (built-in)

## 📝 Notes

- The system runs in an infinite loop
- Press `Ctrl+C` to stop
- Emergency vehicles are randomly triggered (0.5% chance) for demonstration
- Camera updates are commented out but can be enabled by uncommenting `road.cam_update()` in main.py

