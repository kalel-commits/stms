# Smart Traffic Management System - Video Analysis

## 🎯 How It Works

1. **Upload 4 Videos**: Frontend allows uploading 4 videos (one per lane)
2. **AI Analysis**: Backend analyzes each video using YOLO to:
   - Count vehicles
   - Detect emergency vehicles (ambulance, fire truck, police)
3. **Traffic Management**:
   - **Highest Traffic** = Green light (longer duration)
   - **Emergency Vehicle** = Green light (all others red)
   - **Others** = Red light
4. **Real-time Display**: Frontend shows videos with live analysis

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Backend
```bash
cd backend
python app.py
```

### 3. Open Frontend
```
http://localhost:5000
```

### 4. Upload Videos
- Upload 4 videos (one for each lane)
- Click "Start Analysis"
- Watch real-time traffic management!

## 📊 Features

✅ **Video Upload**: Upload 4 sample videos  
✅ **AI Detection**: YOLO-based vehicle counting  
✅ **Emergency Detection**: Automatic ambulance/fire truck detection  
✅ **Smart Signals**: Highest traffic gets green, emergency gets priority  
✅ **Real-time Updates**: Live analysis every 2 seconds  
✅ **Visual Display**: Videos shown with traffic counts and signal status  

## 🔄 Workflow

```
1. User uploads 4 videos → Backend saves them
2. User clicks "Start Analysis" → Backend starts AI processing
3. AI analyzes each video:
   - Counts vehicles
   - Detects emergency vehicles
4. Backend determines:
   - Which lane has highest traffic → GREEN
   - Which lane has emergency → GREEN (others RED)
   - Other lanes → RED
5. Frontend displays:
   - Videos with overlays
   - Vehicle counts
   - Traffic light status
   - Emergency alerts
```

## 📁 File Structure

```
backend/
  ├── app.py              # Flask backend with video analysis
  └── uploads/            # Uploaded videos stored here

frontend/
  ├── index.html          # Video upload & display interface
  ├── styles.css          # Styling
  └── app.js              # Frontend logic
```

## 🎨 Frontend Features

- **Upload Interface**: Drag & drop or click to upload 4 videos
- **Video Display**: Shows all 4 videos with analysis overlays
- **Traffic Lights**: Visual indicators (🟢 Green / 🔴 Red)
- **Statistics**: Total vehicles, emergency count, signal status
- **Real-time Updates**: Automatically refreshes every 2 seconds

## 🔧 API Endpoints

- `POST /api/upload-video` - Upload video for a lane
- `POST /api/start-analysis` - Start AI analysis
- `POST /api/stop-analysis` - Stop analysis
- `GET /api/status` - Get current status
- WebSocket: Real-time updates via Socket.IO

## 💡 Logic

**Traffic Light Priority:**
1. **Emergency Vehicle** (Highest Priority)
   - Lane with emergency → 🟢 GREEN
   - All other lanes → 🔴 RED

2. **Highest Traffic** (Normal Priority)
   - Lane with most vehicles → 🟢 GREEN (longer duration)
   - Other lanes → 🔴 RED

**Green Time Calculation:**
- Base: 30 seconds
- + (Vehicle Count × 1.5 seconds)
- Emergency: Maximum 90 seconds
- Normal: Up to 90 seconds

## 🎬 Example

1. Upload 4 traffic videos
2. Lane 1: 45 vehicles, no emergency
3. Lane 2: 30 vehicles, no emergency
4. Lane 3: 60 vehicles, no emergency ← **Highest traffic**
5. Lane 4: 20 vehicles, **🚨 Ambulance detected** ← **Emergency**

**Result:**
- Lane 4: 🟢 GREEN (Emergency priority)
- Lane 3: 🔴 RED (Emergency overrides highest traffic)
- Lane 1: 🔴 RED
- Lane 2: 🔴 RED

If no emergency:
- Lane 3: 🟢 GREEN (Highest traffic - 60 vehicles)
- Others: 🔴 RED

