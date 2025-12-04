# Low Engagement Detection System - Complete Setup Guide

A real-time emotion detection system that analyzes physiological signals during video viewing to predict user engagement levels.

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **MongoDB** (running on localhost:27017)
- **USB Sensor** (physiological signal sensor with CH340 chip)
- **WSL2** (if on Windows, for USB passthrough)

---

## Quick Start (3 Terminals)

### Terminal 1: MongoDB
```bash
# Start MongoDB (if not already running)
sudo mongod --dbpath /var/lib/mongodb
```

### Terminal 2: Backend API + Signal Collection
```bash
cd /home/kira/personal/surja

# Activate virtual environment
source .venv/bin/activate

# Start signal collection (in background)
python signals.py /dev/ttyUSB0 &

# Start API server
cd api
python server.py
```

### Terminal 3: Frontend
```bash
cd /home/kira/personal/surja/frontend
npm run dev
```

**Access the app at:** http://localhost:5173

---

## Detailed Setup

### 1. MongoDB Setup

```bash
# Install MongoDB (Ubuntu/WSL)
sudo apt update
sudo apt install mongodb

# Start MongoDB
sudo systemctl start mongodb
# OR
sudo mongod --dbpath /var/lib/mongodb

# Verify it's running
mongosh --eval "db.adminCommand('ping')"
```

### 2. Backend Setup

```bash
cd /home/kira/personal/surja

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import tensorflow; import pymongo; import pandas; print('All dependencies OK')"
```

### 3. USB Sensor Setup (WSL2 Only)

On **Windows PowerShell (Admin)**:
```powershell
# List USB devices
& "C:\Program Files\usbipd-win\usbipd.exe" list

# Bind and attach sensor (replace 1-1 with your BUSID)
& "C:\Program Files\usbipd-win\usbipd.exe" bind --busid 1-1
& "C:\Program Files\usbipd-win\usbipd.exe" attach --wsl --busid 1-1
```

On **WSL**:
```bash
# Verify sensor is visible
ls /dev/ttyUSB*

# Grant permissions
sudo chmod a+rw /dev/ttyUSB0
```

### 4. Start Signal Collection

```bash
source .venv/bin/activate
python signals.py /dev/ttyUSB0
# Enter user number when prompted (e.g., 1)
```

### 5. Start API Server

```bash
source .venv/bin/activate
cd api
python server.py
# Server runs on http://localhost:5000
```

### 6. Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
# Frontend runs on http://localhost:5173
```

---

## How It Works

1. **User plays a video** in the frontend
2. **Frontend sends API request** to `/api/video/start`
3. **Backend starts processing**:
   - Reads physiological signals from `signals_data.csv` (populated by `signals.py`)
   - Extracts baseline (first 30 seconds)
   - Calculates change point scores
   - Computes physiological differences
   - Runs LSTM model for emotion prediction
4. **Predictions are stored** in MongoDB
5. **Frontend polls** `/api/predictions/video/<id>` every 5 seconds
6. **Results displayed** on the video timeline

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video/start` | POST | Start processing for a video |
| `/api/video/stop` | POST | Stop processing for a video |
| `/api/predictions/video/<id>` | GET | Get predictions for a video |
| `/api/signals` | GET | Get recent signals |
| `/api/health` | GET | Health check |

---

## Troubleshooting

### "No signals found for video"
- Ensure `signals.py` is running and collecting data
- Check that the sensor is properly connected

### "MongoDB not available"
- Start MongoDB: `sudo mongod --dbpath /var/lib/mongodb`
- Check connection: `mongosh`

### "Permission denied: /dev/ttyUSB0"
```bash
sudo chmod a+rw /dev/ttyUSB0
# For permanent fix:
sudo usermod -aG dialout $USER
# Then restart WSL
```

### Frontend not detecting video play
- Hard refresh browser (Ctrl+Shift+R)
- Check browser console for errors
- Ensure API server is running on port 5000

---

## Project Structure

```
surja/
├── api/                    # Flask API server
│   ├── server.py          # Main API endpoints
│   └── video_session_manager.py  # Video processing logic
├── frontend/              # React frontend
│   └── src/
│       ├── pages/         # VideoLibrary, VideoAnnotation
│       └── components/    # Reusable components
├── docs/                  # Documentation
├── signals.py             # Signal collection script
├── db_models.py           # MongoDB models
├── model_prediction.py    # LSTM prediction logic
├── cal_change_point.py    # Change point detection
├── cal_physiological_diff.py  # Signal processing
└── requirements.txt       # Python dependencies
```

---

## Additional Documentation

- `01_FRONTEND_DOCUMENTATION.md` - Frontend architecture details
- `02_BACKEND_DOCUMENTATION.md` - Backend and ML pipeline details
- `03_INTEGRATION_DOCUMENTATION.md` - API integration guide



