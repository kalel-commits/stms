# Smart Traffic Management System - Full Stack

Complete full-stack application with Frontend, Backend, and AI Model integration.

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Frontend   │◄────►│   Backend   │◄────►│  AI Model   │
│  (React/    │      │   (Flask)   │      │   (YOLO)    │
│   HTML+JS)  │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
      │                    │                     │
      │                    │                     │
      └────────────────────┴─────────────────────┘
                    SQLite Database
```

## 📁 Project Structure

```
Smart-Adaptive-Traffic-Management-System/
├── backend/
│   └── app.py              # Flask backend API
├── frontend/
│   ├── index.html          # Main dashboard HTML
│   ├── styles.css          # Dashboard styling
│   └── app.js              # Frontend JavaScript
├── ai_model.py             # AI detection model
├── road.py                 # Road management logic
├── database.py             # Database operations
├── main.py                 # Original CLI version
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Backend Server

```bash
cd backend
python app.py
```

The backend will start on `http://localhost:5000`

### 3. Open Frontend

Open your browser and navigate to:
```
http://localhost:5000
```

### 4. Start AI Model (Optional)

For each road you want to monitor, run:

```bash
# Using camera
python ai_model.py camera <road_id> <camera_index>

# Using video file
python ai_model.py video <road_id> <video_path>

# Using image
python ai_model.py image <road_id> <image_path>
```

Example:
```bash
python ai_model.py camera 1 0  # Monitor Road 1 with camera 0
python ai_model.py video 2 demo/demo.mp4  # Monitor Road 2 with video
```

## 🎯 Features

### Frontend Dashboard
- ✅ Real-time traffic map with traffic lights
- ✅ Live vehicle count display
- ✅ Emergency vehicle notifications
- ✅ System statistics panel
- ✅ Interactive traffic light control
- ✅ Notification system
- ✅ Responsive design

### Backend API
- ✅ RESTful API endpoints
- ✅ WebSocket for real-time updates
- ✅ Traffic management logic
- ✅ Emergency vehicle prioritization
- ✅ Database integration

### AI Model
- ✅ YOLO-based vehicle detection
- ✅ Emergency vehicle detection
- ✅ Real-time camera/video processing
- ✅ Automatic backend updates

## 📡 API Endpoints

### GET `/api/roads`
Get all roads data

### GET `/api/road/<road_id>`
Get specific road data

### POST `/api/ai/update`
Receive data from AI model
```json
{
  "road_id": 1,
  "vehicle_count": 45,
  "has_emergency": false
}
```

### GET `/api/notifications`
Get all notifications

### GET `/api/statistics`
Get system statistics

### POST `/api/control/switch`
Manually switch traffic light
```json
{
  "road_id": 1
}
```

## 🔄 Data Flow

1. **AI Model** detects vehicles from camera/video
2. **AI Model** sends data to **Backend** via POST `/api/ai/update`
3. **Backend** processes data and updates database
4. **Backend** emits WebSocket events to **Frontend**
5. **Frontend** updates dashboard in real-time

## 🎨 Frontend Features

- **Map View**: Interactive map showing all roads and traffic lights
- **Traffic Lights**: Color-coded (Green/Red/Emergency)
- **Statistics Panel**: Equipment status and fault counts
- **Notifications**: Real-time alerts and updates
- **Manual Control**: Click traffic lights to switch manually

## 🔧 Configuration

### Road Configuration
Edit `backend/app.py` to modify roads:
```python
road1 = Road("Pershore St", 40, 1000, 300, 1)
```

### AI Model Configuration
Edit `ai_model.py` to change:
- Detection region points
- Update interval
- Camera mappings

## 📝 Notes

- The frontend is served by the Flask backend
- WebSocket connection is automatically established
- Database is SQLite (`road.db`)
- YOLO model file (`yolo11n.pt`) must be in project root

## 🐛 Troubleshooting

**Backend won't start:**
- Check if port 5000 is available
- Ensure all dependencies are installed

**Frontend not loading:**
- Check browser console for errors
- Verify backend is running

**AI Model not sending data:**
- Check camera/video path is correct
- Verify backend is running on port 5000
- Check network connectivity

## 📄 License

See LICENSE file for details.

