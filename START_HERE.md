# 🚀 Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start the Backend Server

```bash
cd backend
python app.py
```

Wait for: `Running on http://0.0.0.0:5000`

## Step 3: Open Frontend

Open your browser and go to:
```
http://localhost:5000
```

You should see the **YUNEX TRAFFIC** dashboard!

## Step 4: (Optional) Start AI Model

In a **new terminal**, run:

```bash
# For camera (change road_id and camera_index as needed)
python ai_model.py camera 1 0

# For video file
python ai_model.py video 1 demo/demo.mp4
```

## 🎯 What You'll See

- **Map**: Interactive map with traffic lights
- **Sidebar**: Navigation and statistics
- **Notifications**: Real-time alerts
- **Traffic Lights**: Click to manually switch

## 📊 Features

✅ Real-time traffic monitoring  
✅ Emergency vehicle detection  
✅ Dynamic signal timing  
✅ Interactive dashboard  
✅ WebSocket live updates  

## 🔧 Troubleshooting

**Port 5000 already in use?**
- Change port in `backend/app.py`: `socketio.run(app, port=5001)`

**Frontend not loading?**
- Make sure backend is running
- Check browser console (F12)

**AI model not connecting?**
- Verify backend is running
- Check `API_URL` in `ai_model.py`

---

**Ready to go!** 🎉

