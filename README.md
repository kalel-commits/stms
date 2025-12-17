# Smart Adaptive Traffic Management System

**Intelligent Traffic Control with AI Detection and Blockchain Security**

---

## 📋 Project Overview

A real-time traffic management system that uses **YOLO11 AI** for vehicle detection and a **private blockchain** for secure, immutable record-keeping. The system dynamically adjusts traffic signals based on real-time vehicle density and prioritizes emergency vehicles.

### Key Features

- ✅ **Real-Time Vehicle Detection** - YOLO11 AI detects vehicles in real-time
- ✅ **Adaptive Signal Control** - Dynamic green light timings based on traffic density
- ✅ **Emergency Vehicle Priority** - Automatic signal switching for emergency vehicles
- ✅ **Blockchain Security** - Immutable transaction records for all signal changes
- ✅ **Web Dashboard** - Real-time monitoring and visualization
- ✅ **Multi-Lane Support** - Manages 4 lanes simultaneously

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Modern web browser

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Firebase**
   - **Required**: Set up your own Firebase project (see `FIREBASE_SETUP_INSTRUCTIONS.md`)
   - Create a `.env` file in project root and set:
     ```
     FIREBASE_CREDENTIALS_PATH=path/to/your-firebase-credentials.json
     ```
   - Or set `FIREBASE_CREDENTIALS_PATH` as environment variable
   - Firebase will be initialized automatically on first run
   - **Security**: Never commit Firebase credentials to GitHub!

3. **Start the Server**
   ```bash
   python backend/app.py
   ```

4. **Open in Browser**
   ```
   http://localhost:5000
   ```

### Usage

1. Upload 4 videos (one for each lane)
2. Click "Start Analysis"
3. System automatically detects vehicles and adjusts signals
4. View real-time traffic data and blockchain transactions

---

## 🛠 Technology Stack

- **Backend**: Python, Flask, Flask-SocketIO
- **AI/ML**: YOLO11 (Ultralytics), OpenCV
- **Blockchain**: Custom Python implementation (SHA-256)
- **Database**: Firebase Firestore (Cloud-based)
- **Frontend**: HTML5, CSS3, JavaScript

---

## 📁 Project Structure

```
Smart-Adaptive-Traffic-Management-System/
├── backend/
│   ├── app.py              # Main Flask server
│   └── uploads/            # Video storage
├── frontend/
│   ├── index.html          # Web interface
│   ├── app.js              # Frontend logic
│   └── styles.css          # Styling
├── blockchain.py           # Blockchain implementation
├── database.py             # Firebase Firestore database operations
├── *-firebase-adminsdk-*.json  # Firebase credentials (not included in repo - add your own)
├── requirements.txt        # Dependencies
└── README.md              # This file
```

---

## 🎯 How It Works

1. **Video Upload** → User uploads videos for each lane
2. **AI Detection** → YOLO11 detects vehicles in real-time
3. **Traffic Analysis** → System calculates optimal green times
4. **Signal Control** → Automatically switches signals based on traffic
5. **Blockchain Record** → Every signal change recorded immutably
6. **Real-Time Display** → Live dashboard shows everything

---

## 📡 API Endpoints

### Main Endpoints
- `POST /api/upload-video` - Upload video for lane
- `POST /api/start-analysis` - Start traffic analysis
- `GET /api/status` - Get current system status
- `GET /api/blockchain/stats` - Blockchain statistics
- `GET /api/blockchain/lane/<id>` - Get lane transactions

See `PROJECT_DETAILS.md` for complete API documentation.

---

## ⛓ Blockchain Features

- **Immutable Records** - All signal changes recorded as transactions
- **Tamper-Proof** - SHA-256 cryptographic hashing
- **Real-Time Updates** - Transactions recorded automatically
- **Complete Audit Trail** - Full history of all decisions
- **Private Blockchain** - Fast, free, and secure

---

## 📚 Documentation

- **Detailed Documentation**: See `PROJECT_DETAILS.md` for complete information
  - Architecture details
  - Complete API reference
  - Configuration options
  - Troubleshooting guide

---

## 🔧 Configuration

Default settings in `backend/app.py`:
- **Port**: 5000
- **Blockchain Difficulty**: 2
- **Block Size**: 5 transactions
- **Frame Skip**: Every 3rd frame
- **Confidence Threshold**: 0.25 (25%)

---

## 🐛 Troubleshooting

**Firebase errors?**
- Ensure Firebase credentials file exists in project root
- Check that `firebase-admin` is installed: `pip install firebase-admin`
- Download Firebase service account credentials from Firebase Console
- Create `.env` file with `FIREBASE_CREDENTIALS_PATH` pointing to your credentials file
- **Important**: Never commit Firebase credentials to GitHub

**Videos not uploading?**
- Check file format (MP4, AVI, MOV, MKV, WebM)
- Ensure backend server is running

**Analysis not starting?**
- Make sure all 4 videos are uploaded
- Check browser console for errors

**Port already in use?**
- Change port in `backend/app.py` or stop other applications

---

## 📝 License

This project is for educational and demonstration purposes.

---

## 👥 Contact

For detailed documentation, see `PROJECT_DETAILS.md`

---

**Version**: 1.0.0  
**Last Updated**: January 2024
