# 🚀 Quick Start Guide

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Start Backend Server
```bash
cd backend
python app.py
```

You should see:
```
Starting server on http://localhost:5000
```

## Step 3: Open Frontend
Open your browser and go to:
```
http://localhost:5000
```

## Step 4: Upload 4 Videos
1. Click on each "Lane" card to upload a video
2. Upload 4 different traffic videos (one per lane)
3. Wait for all 4 videos to be uploaded
4. Click "Start Analysis" button

## Step 5: Watch the Magic! ✨
- Videos will be analyzed in real-time
- Vehicle counts will appear on each video
- Traffic lights will automatically adjust:
  - **Highest traffic** → 🟢 GREEN
  - **Emergency vehicle** → 🟢 GREEN (others 🔴 RED)
  - **Others** → 🔴 RED

## 📊 What You'll See

- **4 Video Cards**: Each showing a lane with live analysis
- **Vehicle Counts**: Real-time vehicle detection
- **Traffic Lights**: Visual indicators (🟢/🔴)
- **Emergency Alerts**: When ambulance/fire truck detected
- **Statistics Panel**: Total vehicles, emergency count, etc.

## 🎯 How It Works

1. **Upload**: You upload 4 sample videos
2. **AI Analysis**: YOLO model analyzes each video:
   - Counts vehicles (cars, buses, trucks, bikes)
   - Detects emergency vehicles (ambulance, fire truck, police)
3. **Smart Signals**: 
   - Lane with **highest traffic** = 🟢 GREEN (longer time)
   - Lane with **emergency** = 🟢 GREEN (all others 🔴 RED)
   - Other lanes = 🔴 RED
4. **Real-time Updates**: Analysis updates every 2 seconds

## 💡 Example Scenario

**Lane 1**: 30 vehicles, no emergency  
**Lane 2**: 45 vehicles, no emergency  
**Lane 3**: 60 vehicles, no emergency ← **Highest**  
**Lane 4**: 20 vehicles, 🚨 **Ambulance detected** ← **Emergency**

**Result:**
- Lane 4: 🟢 GREEN (Emergency priority - all others red)
- Lane 3: 🔴 RED (Emergency overrides highest traffic)
- Lane 1: 🔴 RED
- Lane 2: 🔴 RED

**If no emergency:**
- Lane 3: 🟢 GREEN (Highest traffic - 60 vehicles)
- Others: 🔴 RED

## 🐛 Troubleshooting

**Videos not uploading?**
- Check file format (mp4, avi, mov, mkv, webm)
- Check browser console for errors

**Analysis not starting?**
- Make sure all 4 videos are uploaded
- Check backend console for errors

**Videos not displaying?**
- Check that backend is running
- Check browser console (F12)

---

**Ready to manage traffic!** 🚦

