# Low Engagement Detection System - Concise Documentation

A real-time emotion detection system that analyzes physiological signals (GSR, HR) during video viewing to predict user engagement levels using LSTM models and K-means clustering.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Frontend Components](#frontend-components)
7. [Backend Modules](#backend-modules)
8. [Database Schema](#database-schema)
9. [ML Pipeline](#ml-pipeline)
10. [API Reference](#api-reference)
11. [Configuration](#configuration)
12. [Troubleshooting](#troubleshooting)

---

## System Overview

### What It Does
- Collects physiological signals (GSR, HR) from wearable sensors
- Processes signals using change point detection (RuLSIF)
- Predicts emotions using K-means clustering + LSTM models
- Displays real-time predictions on a color-coded video timeline
- Supports manual emotion annotation for research validation

### Emotion Categories
| Code | Emotion | Valence | Arousal | Color |
|------|---------|---------|---------|-------|
| HH | Happy | High | High | `#eecdac` (Beige) |
| HL | Neutral | High | Low | `#7fc087` (Green) |
| LH | Angry | Low | High | `#f4978e` (Pink) |
| LL | Sad | Low | Low | `#879af0` (Blue) |

---

## Quick Start

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** and npm
- **MongoDB** (localhost:27017)
- **USB Sensor** (physiological signal sensor with CH340 chip)
- **WSL2** (if on Windows, for USB passthrough)

### Terminal 1: MongoDB
```bash
sudo mongod --dbpath /var/lib/mongodb
```

### Terminal 2: Backend API + Signal Collection
```bash
cd /home/kira/personal/surja
source .venv/bin/activate
python signals.py /dev/ttyUSB0 &   # Signal collection (background)
cd api && python server.py          # API server (port 5000)
```

### Terminal 3: Frontend
```bash
cd /home/kira/personal/surja/frontend
npm run dev   # Runs on http://localhost:5173
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │            React Frontend (localhost:5173)                  │  │
│  │  • Video playback • Emotion timeline • Manual annotations  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│   Flask Backend      │              │  FastAPI Backend     │
│   (localhost:5000)   │              │  (localhost:8000)    │
│                      │              │                      │
│  • Video sessions    │              │  • User auth (JWT)   │
│  • Signal processing │              │  • Manual            │
│  • ML predictions    │              │    annotations (CSV) │
└──────────┬───────────┘              └──────────────────────┘
           │ PyMongo
           ▼
┌──────────────────────────────────────┐
│           MongoDB                     │
│        (localhost:27017)              │
│  • signals • predictions • features  │
└──────────────────────────────────────┘
           ▲
           │
┌──────────┴───────────┐
│   USB Sensor         │
│   (GSR, HR data)     │
└──────────────────────┘
```

### Data Flow
```
1. User plays video → Frontend calls /api/video/start
2. Backend records video start in MongoDB
3. signals.py collects sensor data → MongoDB + CSV
4. main.py triggers 5-second windowing
5. cal_change_point.py calculates change scores (RuLSIF)
6. cal_physiological_diff.py extracts features
7. model_prediction.py runs K-means + LSTM → predictions
8. Frontend polls /api/predictions/video/<id> every 5 seconds
9. SegmentedProgressBar displays color-coded timeline
```

---

## Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 + TypeScript | UI framework |
| Vite 5 | Build tool & dev server |
| TanStack Query | Server state management |
| ShadCN UI + Tailwind CSS | UI components & styling |
| React Router 6 | Client-side routing |

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Primary language |
| Flask 3.x | REST API framework |
| TensorFlow/Keras 2.x | LSTM models |
| Scikit-learn | K-means clustering |
| NumPy/Pandas | Data processing |

### Database
| Technology | Purpose |
|------------|---------|
| MongoDB 6.x | NoSQL database |
| PyMongo | Python MongoDB driver |

---

## Project Structure

```
surja/
├── api/                          # Flask API server
│   ├── server.py                 # Main API endpoints
│   └── video_session_manager.py  # Video session handling
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── video/
│   │   │       ├── video-player.tsx
│   │   │       ├── SegmentedProgressBar.tsx
│   │   │       └── annotation-timeline.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── VideoLibrary.tsx
│   │   │   └── VideoAnnotation.tsx
│   │   ├── lib/
│   │   │   └── backend-api.ts    # Backend API client
│   │   └── config/
│   │       └── videos.ts         # Video metadata
│   └── annotations-backend/      # FastAPI for manual annotations
│
├── model/                        # ML models
│   ├── lstm_HH.h5, lstm_HL.h5, lstm_LH.h5, lstm_LL.h5
│   ├── kmeans_model.pkl
│   └── scaler.pkl
│
├── signals.py                    # Signal collection script
├── main.py                       # Main orchestrator & file watcher
├── cal_change_point.py           # Change point detection (RuLSIF)
├── cal_physiological_diff.py     # Feature extraction
├── model_prediction.py           # LSTM prediction logic
├── db_config.py                  # MongoDB configuration
├── db_models.py                  # Database access layer
└── requirements.txt              # Python dependencies
```

---

## Frontend Components

### Key Pages

| Page | Route | Purpose |
|------|-------|---------|
| Login | `/login` | User authentication (JWT) |
| Dashboard | `/dashboard` | Welcome + stats |
| Video Library | `/video-library` | Browse available videos |
| Video Annotation | `/video/:videoId` | Main annotation interface |

### Video Annotation Features
- **Three viewing modes:** Full A/V, Video Only, Audio Only
- **Automatic predictions:** Real-time LSTM predictions displayed as colored segments
- **Manual annotations:** Click-to-annotate timeline per mode
- **Session management:** Start/stop video processing

### Key Components

**SegmentedProgressBar** - Displays emotion predictions
```typescript
interface PredictionSegment {
  segment_index: number;
  timestamp: number;
  probe: 'HH' | 'HL' | 'LH' | 'LL';
  emotion: 'Happy' | 'Neutral' | 'Angry' | 'Sad';
  color: string;
}
```

**VideoPlayer** - Custom video player with enhanced controls
```typescript
interface VideoPlayerProps {
  src: string;
  onTimeUpdate: (time: number) => void;
  onPlay?: () => void;
  onPause?: () => void;
  forceMuted?: boolean;     // Video Only mode
  hideVideo?: boolean;      // Audio Only mode
}
```

---

## Backend Modules

### signals.py
**Purpose:** Real-time physiological signal collection
- Reads sensor data (GSR, HR) in real-time
- Buffers data for 5 seconds
- Dual-write: CSV + MongoDB
- User-specific data tagging

### cal_change_point.py
**Purpose:** Change point detection using RuLSIF algorithm
- Detects sudden changes in physiological patterns
- Sliding window approach
- Output: Change score (0.0 - 1.0+)

### cal_physiological_diff.py
**Purpose:** Feature extraction from baseline
- Calculates difference from baseline (Video 0)
- Assigns valence/arousal to videos
- Output: `gsr_diff`, `hr_diff`, `valence`, `arousal`

### model_prediction.py
**Purpose:** Emotion prediction
- K-means clustering (3 clusters) for user profiling
- LSTM models (4 separate) for each emotion category
- Prediction stored in MongoDB with dual storage:
  - `predictions` collection (permanent)
  - `active_predictions` collection (TTL: 1 hour)

---

## Database Schema

**Database:** `engagement_db` | **Connection:** `mongodb://localhost:27017`

### Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `signals` | Raw physiological signals | `time_series`, `gsr`, `hr`, `timestamp`, `user_id`, `session_id` |
| `video_starts` | Video start events | `video_id`, `timestamp`, `user_id`, `session_id` |
| `windowed_data` | 5-second windowed signals | `window_id`, `gsr_avg`, `hr_avg` |
| `change_scores` | Change point scores | `time_series`, `score`, `user_id` |
| `features` | Extracted features | `video_no`, `gsr_diff`, `hr_diff`, `valence`, `arousal` |
| `predictions` | Permanent prediction log | `starttime`, `video_no`, `probe`, `cluster_id`, `user_id` |
| `active_predictions` | Frontend predictions (TTL 1h) | Same as predictions |

### Session ID Format
```
{user_id}_{video_id}_{timestamp}
Example: user1_2_1732178316000
```

---

## ML Pipeline

```
Raw Signals → Windowing (5s) → Change Detection → Feature Extraction → ML Prediction
(signals.py)    (main.py)     (cal_change_point)  (cal_phys_diff)    (model_pred)
```

### Pipeline Steps

1. **Data Windowing:** 5-second windows
2. **Change Point Detection (RuLSIF):** Detect sudden physiological changes
3. **Feature Extraction:** `gsr_diff`, `hr_diff` from baseline
4. **K-means Clustering:** Assign user to 1 of 3 clusters
5. **LSTM Prediction:** Run 4 LSTM models, select highest probability

### LSTM Architecture
```
Input → LSTM(64 units) → Dropout(0.2) → Dense(1, sigmoid)
```

### Model Files
```
model/lstm_HH.h5  → Happy prediction
model/lstm_HL.h5  → Neutral prediction
model/lstm_LH.h5  → Angry prediction
model/lstm_LL.h5  → Sad prediction
model/kmeans_model.pkl → User clustering
model/scaler.pkl → Feature scaling
```

---

## API Reference

**Base URL:** `http://localhost:5000`

### Video Session

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video/<id>/start` | POST | Start video processing |
| `/api/video/<id>/stop` | POST | Stop video processing |

**Start Video Request:**
```json
{
  "video_id": 2,
  "timestamp": 1732178316000,
  "user_id": "user1",
  "session_id": "user1_2_1732178316000"
}
```

### Predictions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predictions/video/<id>` | GET | Get predictions for video |
| `/api/predictions/active` | GET | Get active predictions |

**Get Predictions Response:**
```json
{
  "success": true,
  "video_id": 2,
  "segments": [
    {
      "segment_index": 0,
      "timestamp": 1732178316000,
      "probe": "HH",
      "emotion": "Happy",
      "color": "#eecdac"
    }
  ],
  "total": 36
}
```

### Utility

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/signals` | GET | Get recent signals |
| `/api/health` | GET | Health check |
| `/api/session/summary/<id>` | GET | Get session statistics |

### Annotations API (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | POST | User authentication |
| `/register` | POST | User registration |
| `/annotations/<video_name>` | GET | Fetch annotations |
| `/annotations/<video_name>` | POST | Save annotations |

---

## Configuration

### Video Configuration (`frontend/src/config/videos.ts`)
```typescript
export const VIDEO_CONFIGS: VideoConfig[] = [
  { id: "video1", backendId: 1, name: "Baseline", duration: 180, path: "/assets/videos/0.mp4" },
  { id: "video2", backendId: 2, name: "Stimulus 1", duration: 151, path: "/assets/videos/1.mp4" },
  // ...
];
```

### Environment Variables

**Frontend (`.env`):**
```env
VITE_BACKEND_API_URL=http://localhost:5000
VITE_ANNOTATIONS_API_URL=http://localhost:8000
```

**Backend (`.env`):**
```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=engagement_db
FLASK_SECRET_KEY=your-secret-key
```

### Video Durations (`api/server.py`)
```python
video_durations = {
    1: 180000,  # 3 minutes
    2: 151000,  # 2:31
    3: 160000,  # 2:40
    4: 115000   # 1:55
}
```

---

## Troubleshooting

### MongoDB Issues

**"MongoDB not available"**
```bash
# Start MongoDB
sudo mongod --dbpath /var/lib/mongodb

# Verify connection
mongosh --eval "db.adminCommand('ping')"
```

**Check data exists:**
```bash
mongosh engagement_db
db.predictions.countDocuments({user_id: "user1"})
```

### USB Sensor Issues (WSL2)

**"Permission denied: /dev/ttyUSB0"**
```bash
sudo chmod a+rw /dev/ttyUSB0
# Permanent fix:
sudo usermod -aG dialout $USER
```

**Attach USB in WSL2 (Windows PowerShell Admin):**
```powershell
& "C:\Program Files\usbipd-win\usbipd.exe" list
& "C:\Program Files\usbipd-win\usbipd.exe" bind --busid 1-1
& "C:\Program Files\usbipd-win\usbipd.exe" attach --wsl --busid 1-1
```

### API Issues

**CORS Errors**
```python
# Ensure CORS is enabled in api/server.py
from flask_cors import CORS
CORS(app, origins=['http://localhost:5173'])
```

**Predictions Not Showing**
```bash
# 1. Check API directly
curl http://localhost:5000/api/predictions/video/2?user_id=user1

# 2. Check MongoDB
python scripts/verify_mongodb.py --users

# 3. Check backend logs
tail -f api/logs/api.log
```

### Frontend Issues

**Video Not Loading**
- Check video path in `videos.ts` matches actual file in `public/assets/videos/`

**Authentication Failed**
```javascript
// Clear localStorage and re-login
localStorage.clear()
```

**Polling Not Working**
- Check browser DevTools → Network tab for API calls
- Verify `backendVideoId` and `userId` are correct

---

## Development Commands

### Backend
```bash
# Setup
cd /home/kira/personal/surja
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
python signals.py /dev/ttyUSB0  # Signal collection
python main.py                   # Main orchestrator
cd api && python server.py       # API server
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # Development
npm run build   # Production build
npm run preview # Preview build
```

### Database
```bash
# Initialize indexes
python -c "from db_config import initialize_indexes; initialize_indexes()"

# Populate test data
python scripts/migrate_test_data.py

# Verify data
python scripts/verify_mongodb.py --all
```

---

## User Session Lifecycle

```
1. Login → Store username & token in localStorage
2. Video Selection → Navigate to /video/:videoId
3. Video Play → Generate session_id → POST /api/video/start → Start processing
4. During Playback → Poll predictions every 5s → Update visualization
5. Video Pause/End → POST /api/video/stop → Stop processing
6. Logout → Clear localStorage
```

---

**Last Updated:** December 2025  
**Version:** 2.0.0



