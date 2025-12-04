# 🔧 Backend Documentation - Annotation App

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Core Modules](#core-modules)
6. [Database](#database)
7. [Machine Learning Pipeline](#machine-learning-pipeline)
8. [API Endpoints](#api-endpoints)
9. [Configuration](#configuration)
10. [Development Guide](#development-guide)
11. [Deployment](#deployment)

---

## Overview

The Annotation App backend is a Python-based real-time emotion analysis system that:

- Collects physiological signals (GSR, HR) from wearable sensors
- Processes signals using machine learning models
- Predicts opportune moments for emotional interventions
- Stores data in MongoDB with user separation
- Exposes REST API for frontend integration

**Location:** `/home/kira/personal/surja/`

**Core Function:** Real-time physiological signal processing and emotion prediction

---

## Architecture

### **System Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    Annotation App Backend                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Sensors    │ ───► │   Signals    │ ───► │   MongoDB    │
│  (GSR, HR)   │      │  Processing  │      │   Database   │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                             │
                             ▼
                      ┌──────────────┐
                      │   ML Models  │
                      │  (K-means +  │
                      │     LSTM)    │
                      └──────────────┘
                             │
                             │
                             ▼
                      ┌──────────────┐      ┌──────────────┐
                      │  Predictions │ ───► │  Flask API   │
                      │   Storage    │      │  (Port 5000) │
                      └──────────────┘      └──────────────┘
                                                   │
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │   Frontend   │
                                            │  (React App) │
                                            └──────────────┘
```

### **Data Flow**

```
1. Video starts → Frontend calls /api/video/<id>/start
2. Backend records video start in MongoDB
3. Backend triggers processing pipeline
4. Sensors generate GSR/HR data
5. signals.py collects and stores signals (CSV + MongoDB)
6. main.py triggers windowing (5-second windows)
7. cal_change_point.py calculates change scores
8. cal_physiological_diff.py extracts features
9. model_prediction.py runs ML models
10. Predictions stored in MongoDB (active_predictions collection)
11. Frontend polls /api/predictions/video/<id>
12. Frontend displays color-coded timeline
```

---

## Technology Stack

### **Core Technologies**

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Primary language |
| **MongoDB** | 6.x | NoSQL database |
| **Flask** | 3.x | REST API framework |
| **NumPy** | Latest | Numerical computing |
| **Pandas** | Latest | Data manipulation |
| **Scikit-learn** | Latest | ML models (K-means) |
| **TensorFlow/Keras** | 2.x | LSTM models |

### **Key Libraries**

| Library | Purpose |
|---------|---------|
| **pymongo** | MongoDB driver |
| **flask-cors** | CORS support |
| **watchdog** | File system monitoring |
| **joblib** | Model serialization |
| **scipy** | Scientific computing |

---

## Project Structure

```
backend/
├── signals.py                    # Signal collection & storage
├── main.py                       # Main orchestrator & file watcher
├── cal_change_point.py          # Change point detection (RuLSIF)
├── cal_physiological_diff.py    # Feature extraction
├── model_prediction.py          # ML prediction (LSTM + K-means)
│
├── db_config.py                 # MongoDB configuration
├── db_models.py                 # Database access layer
├── DATABASE_SCHEMA.md           # Database schema documentation
│
├── api/
│   ├── server.py                # Flask REST API
│   ├── video_session_manager.py # Video session handling
│   ├── API_DOCUMENTATION.md     # API documentation
│   └── README.md                # API quick start
│
├── 3_pwindow_lstm_model0.h5    # LSTM model for user cluster 0
├── 3_pwindow_lstm_model1.h5    # LSTM model for user cluster 1
├── model/                       # Archived/backup models
│
├── scripts/
│   ├── migrate_test_data.py    # Populate test data
│   ├── verify_mongodb.py       # Verify database
│   └── ...
│
├── data/                        # Data storage (CSV backups)
│   ├── signals_data.csv
│   ├── signals_data.txt
│   ├── pred.csv
│   ├── features.csv
│   └── ...
│
├── venv_db/                     # Python virtual environment
├── requirements_db.txt          # Python dependencies
└── README.md                    # Project README
```

---

## Core Modules

### **1. signals.py**

**Purpose:** Real-time physiological signal collection and storage.

**Key Functions:**
```python
def insert_signals_bulk(signal_data: list) -> bool
```
Bulk insert signals into MongoDB (dual-write with CSV).

**Features:**
- Reads sensor data (GSR, HR) in real-time
- Buffers data for 5 seconds
- Dual-write: CSV + MongoDB
- User-specific data tagging

**Data Format:**
```
time_series, gsr, hr, timestamp, datetime
1, 250, 70, 1732178316000, 2025-11-21 09:48:36
2, 251, 71, 1732178317000, 2025-11-21 09:48:37
```

**MongoDB Document:**
```python
{
  'time_series': 1,
  'gsr': 250,
  'hr': 70,
  'timestamp': 1732178316000,
  'datetime': '2025-11-21 09:48:36',
  'user_id': 'user1',
  'session_id': 'user1_1_1732178316000',
  'created_at': ISODate("2025-11-21T09:48:36Z")
}
```

**Execution:**
```bash
python signals.py
```

---

### **2. main.py**

**Purpose:** Main orchestrator - file watching, data windowing, ML pipeline triggering.

**Key Functions:**
```python
def on_created(event)
def on_modified(event)
def process_video_data(v_no, start_time)
```

**Features:**
- Watches `data/` directory for new signal files
- Detects video starts
- Triggers windowing (5-second windows)
- Coordinates ML pipeline
- Records video starts in MongoDB

**File Watching:**
```python
# Monitors these files
- signals_data.txt  # Sensor data
- video_start.txt   # Video start events
```

**Execution:**
```bash
python main.py
```

---

### **3. cal_change_point.py**

**Purpose:** Change point detection using Density Ratio Estimation (RuLSIF).

**Algorithm:** RuLSIF (Relative Unconstrained Least-Squares Importance Fitting)

**Key Functions:**
```python
def cal_change_point_score(data_path: str) -> np.ndarray
```

**Features:**
- Detects significant changes in physiological signals
- Sliding window approach
- Dual-write: CSV + MongoDB

**Output:**
```python
{
  'time_series': 10,
  'score': 0.75,
  'user_id': 'user1',
  'session_id': 'user1_1_1732178316000',
  'created_at': ISODate(...)
}
```

---

### **4. cal_physiological_diff.py**

**Purpose:** Feature extraction - calculates physiological changes from baseline.

**Key Functions:**
```python
def cal_physiological_difference(gsr_input, hr_input, v_no, v_type)
```

**Features:**
- Calculates difference from baseline (Video 0)
- Assigns valence/arousal to videos
- Stores features for ML models
- Dual-write: CSV + MongoDB

**Video Valence/Arousal Mapping:**
```python
video_valence_arousal = {
    0: {'valence': 0, 'arousal': 0},  # Baseline
    1: {'valence': 1, 'arousal': 1},  # High-High (Happy)
    2: {'valence': 1, 'arousal': 0},  # High-Low (Neutral)
    3: {'valence': 0, 'arousal': 1},  # Low-High (Angry)
    4: {'valence': 0, 'arousal': 0},  # Low-Low (Sad)
}
```

**Output Features:**
```python
{
  'video_no': 2,
  'gsr_diff': 15.3,
  'hr_diff': 8.7,
  'valence': 1,
  'arousal': 0,
  'start_time': 1732178316000,
  'user_id': 'user1',
  'session_id': 'user1_2_1732178616000',
  'created_at': ISODate(...)
}
```

---

### **5. model_prediction.py**

**Purpose:** Emotion prediction using K-means clustering + LSTM models.

**ML Models:**
1. **User Clustering** - User profiling (2 pre-defined clusters)
2. **LSTM Models** - Two models (one per user cluster), each predicting 4 emotion classes

**Key Functions:**
```python
def get_model_prediction(test, nearest_centroid_index, starttime, v_no, user_id, session_id)
```

**Prediction Flow:**
```
1. Load user features (GSR diff, HR diff)
2. Assign to nearest K-means cluster
3. Select appropriate LSTM model
4. Predict emotion (HH, HL, LH, LL)
5. Store prediction in MongoDB
```

**LSTM Model Files:**
```
3_pwindow_lstm_model0.h5  → LSTM for user cluster 0 (predicts all 4 emotions)
3_pwindow_lstm_model1.h5  → LSTM for user cluster 1 (predicts all 4 emotions)
```

**Emotion Labels:**
```python
'HH': High Valence, High Arousal    → Happy
'HL': High Valence, Low Arousal     → Neutral
'LH': Low Valence, High Arousal     → Angry
'LL': Low Valence, Low Arousal      → Sad
```

**Prediction Output:**
```python
{
  'starttime': 1732178316000,
  'video_no': 2,
  'probe': 'HH',
  'cluster_id': 1,
  'user_id': 'user1',
  'session_id': 'user1_2_1732178616000',
  'created_at': ISODate(...)
}
```

**Dual Storage:**
- `predictions` collection - Permanent log
- `active_predictions` collection - For frontend (TTL: 1 hour)

---

## Database

### **MongoDB Configuration**

**Connection:** `mongodb://localhost:27017`  
**Database:** `engagement_db`

**Configuration File:** `db_config.py`

```python
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "engagement_db"

def get_db():
    """Get MongoDB database connection (singleton pattern)"""
    return DatabaseConnection.get_database()
```

### **Collections**

| Collection | Purpose | Documents |
|------------|---------|-----------|
| **signals** | Raw physiological signals | ~600/user/video |
| **video_starts** | Video start events | 1/video/user |
| **windowed_data** | 5-second windowed signals | ~36/video |
| **change_scores** | Change point scores | ~36/video |
| **features** | Extracted features | ~36/video |
| **predictions** | Permanent prediction log | ~36/video/user |
| **active_predictions** | Frontend predictions (TTL) | ~36/video/user |

**See:** `DATABASE_SCHEMA.md` for detailed schema.

### **User Separation**

All collections include:
```python
'user_id': str      # User identifier
'session_id': str   # Unique session ID
```

**Session ID Format:**
```
{user_id}_{video_id}_{timestamp}
# Example: user1_2_1732178316000
```

### **Indexes**

**Performance Optimization:**
```python
# Compound indexes
predictions: { user_id: 1, video_no: 1 }
active_predictions: { user_id: 1, video_no: 1 }

# TTL index (auto-delete after 1 hour)
active_predictions: { created_at: 1 }, expireAfterSeconds=3600
```

### **Database Access Layer**

**File:** `db_models.py`

**Key Functions:**
```python
# Signals
insert_signal(time_series, gsr, hr, timestamp, datetime_str, user_id, session_id)
insert_signals_bulk(signal_data)
get_signals_by_timestamp_range(start_ts, end_ts, user_id, session_id)

# Video Starts
insert_video_start(timestamp, video_id, user_id, session_id)
get_latest_video_start(user_id, session_id)

# Predictions
insert_prediction(starttime, video_no, probe, cluster_id, user_id, session_id)
insert_active_prediction(starttime, video_no, probe, user_id, session_id)
get_predictions_by_video_id(video_id, user_id, session_id)
clear_active_predictions(user_id, session_id)

# Features
insert_feature(video_no, gsr_diff, hr_diff, valence, arousal, start_time, user_id, session_id)
get_features_by_video(video_no, user_id, session_id)

# Statistics
get_database_stats()
```

**User-Specific Queries:**
```python
# Get predictions for specific user and video
predictions = get_predictions_by_video_id(
    video_id=2, 
    user_id='user1', 
    session_id=None  # All sessions
)
```

---

## Machine Learning Pipeline

### **Pipeline Overview**

```
Raw Signals → Windowing → Change Detection → Feature Extraction → ML Prediction
(signals.py)   (main.py)   (change_point)    (phys_diff)         (model_pred)
```

### **1. Data Windowing**

**Window Size:** 5 seconds (configurable)

```python
# main.py
window_size = 5  # seconds
for window in create_windows(signals, window_size):
    process_window(window)
```

### **2. Change Point Detection (RuLSIF)**

**Algorithm:** Relative Unconstrained Least-Squares Importance Fitting

**Purpose:** Detect sudden changes in physiological patterns

**Parameters:**
```python
alpha = 0.1       # Regularization
window_size = 10  # Samples for comparison
```

**Output:** Change score (0.0 - 1.0+)

### **3. Feature Extraction**

**Features per window:**
- `gsr_diff` - Difference from baseline GSR
- `hr_diff` - Difference from baseline HR
- `valence` - Emotional valence (0 or 1)
- `arousal` - Emotional arousal (0 or 1)

### **4. User Cluster Assignment**

**Purpose:** User profiling based on physiological responses

**Implementation:** Hardcoded centroids in `profile_cluster_creation.py`

**Parameters:**
```python
# 2 pre-defined cluster centroids (8-dimensional vectors)
cluster_centroid = np.array([
    [0.132, 0.116, 0.124, 0.104, 0.135, 0.129, 0.136, 0.120],  # Cluster 0
    [0.325, 0.219, 0.364, 0.228, 0.352, 0.215, 0.313, 0.206]   # Cluster 1
])
```

**Output:** Cluster ID (0 or 1)

### **5. LSTM Prediction**

**Architecture:**
```
Input Layer → LSTM(64 units) → Dropout(0.2) → Dense(1, sigmoid)
```

**Models:** 2 LSTM models (one per user cluster), each outputs 4 emotion classes

**Input Shape:** `(sequence_length, n_features)`

**Output:** Probability (0.0 - 1.0)

**Prediction Logic:**
```python
# Load model based on user's cluster assignment
loaded_model = load_model(f"3_pwindow_lstm_model{nearest_centroid_index}.h5",
                          custom_objects={'PReLU': PReLU})

# Model outputs probabilities for all 4 classes
y_preds = loaded_model.predict(features)

# Select class with highest probability
y_pred_class = np.argmax(y_preds, axis=1)

# Map to emotion labels
labels = ["HH", "HL", "LH", "LL"]
predicted_emotion = labels[y_pred_class[0]]
```

---

## API Endpoints

**Flask API:** `api/server.py`  
**Base URL:** `http://localhost:5000`

### **Video Session Management**

**Start Video Processing**
```http
POST /api/video/<int:video_id>/start

Request Body:
{
  "video_id": 2,
  "timestamp": 1732178316000,
  "user_id": "user1",
  "session_id": "user1_2_1732178316000"
}

Response:
{
  "success": true,
  "message": "Video session started",
  "session_id": "user1_2_1732178316000"
}
```

**Stop Video Processing**
```http
POST /api/video/<int:video_id>/stop

Request Body:
{
  "session_id": "user1_2_1732178316000"
}

Response:
{
  "success": true,
  "message": "Video session stopped"
}
```

### **Predictions**

**Get Active Predictions**
```http
GET /api/predictions/active?user_id=user1

Response:
{
  "success": true,
  "predictions": [
    {
      "starttime": 1732178316000,
      "video_no": 2,
      "probe": "HH",
      "cluster_id": 1
    }
  ],
  "total": 36
}
```

**Get Video Predictions**
```http
GET /api/predictions/video/<int:video_id>?user_id=user1

Response:
{
  "success": true,
  "video_id": 2,
  "segments": [
    {
      "segment_index": 0,
      "timestamp": 1732178316000,
      "probe": "HH",
      "emotion": "Happy",
      "color": "#eecdac",
      "cluster_id": 1
    }
  ],
  "total": 36,
  "duration_ms": 151000
}
```

### **Statistics**

**Get Session Summary**
```http
GET /api/session/summary/<int:video_id>?user_id=user1

Response:
{
  "success": true,
  "video_id": 2,
  "statistics": {
    "total_segments": 36,
    "emotion_distribution": {
      "Happy": 12,
      "Neutral": 10,
      "Angry": 8,
      "Sad": 6
    },
    "average_gsr": 255.3,
    "average_hr": 75.2
  }
}
```

**Health Check**
```http
GET /api/health

Response:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-21T12:00:00Z"
}
```

**See:** `api/API_DOCUMENTATION.md` for complete API reference.

---

## Configuration

### **Database Configuration**

**File:** `db_config.py`

```python
# MongoDB settings
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "engagement_db"

# Enable/disable database writes
DB_ENABLED = True

# Collections
COLLECTIONS = {
    'signals': 'signals',
    'video_starts': 'video_starts',
    'windowed_data': 'windowed_data',
    'change_scores': 'change_scores',
    'features': 'features',
    'predictions': 'predictions',
    'active_predictions': 'active_predictions'
}
```

### **Video Configuration**

**File:** `api/server.py`

```python
# Video durations (milliseconds)
video_durations = {
    1: 180000,  # 3 minutes
    2: 151000,  # 2:31
    3: 160000,  # 2:40
    4: 115000   # 1:55
}
```

### **Model Paths**

```python
# model_prediction.py
# Models are loaded based on user cluster assignment
# nearest_centroid_index is 0 or 1
loaded_model = load_model(f"3_pwindow_lstm_model{nearest_centroid_index}.h5",
                          custom_objects={'PReLU': PReLU})

# Note: K-means centroids are hardcoded in profile_cluster_creation.py
# No external .pkl files are used
```

---

## Development Guide

### **Setup**

```bash
cd /home/kira/personal/surja

# Create virtual environment
python3 -m venv venv_db

# Activate virtual environment
source venv_db/bin/activate

# Install dependencies
pip install -r requirements_db.txt
```

### **Dependencies**

**Core:**
```
pymongo==4.6.0
flask==3.0.0
flask-cors==4.0.0
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
tensorflow==2.15.0
```

**Utilities:**
```
watchdog==3.0.0
joblib==1.3.2
scipy==1.11.3
tabulate==0.9.0
```

### **Start MongoDB**

```bash
# Start MongoDB (WSL2)
mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork

# Check status
ps aux | grep mongod
```

### **Initialize Database**

```bash
# Create indexes
python -c "from db_config import initialize_indexes; initialize_indexes()"

# Populate test data
python scripts/migrate_test_data.py

# Verify data
python scripts/verify_mongodb.py --all
```

### **Start Backend Services**

```bash
# Terminal 1: Flask API
source venv_db/bin/activate
cd api
python server.py

# Terminal 2: Main processing pipeline
source venv_db/bin/activate
python main.py

# Terminal 3: Signal collection (if using real sensors)
source venv_db/bin/activate
python signals.py
```

### **Testing**

```bash
# Test MongoDB connection
python test_database.py

# Test API endpoints
python api/test_api.py

# Verify user separation
python scripts/verify_mongodb.py --users
```

### **Debugging**

**Enable detailed logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check logs:**
```bash
# API logs
tail -f api/logs/api.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

**MongoDB shell queries:**
```bash
mongosh engagement_db

# Check collections
db.getCollectionNames()

# Count documents
db.predictions.countDocuments()

# Find user data
db.predictions.find({user_id: "user1"}).limit(5)
```

---

## Deployment

### **Production Checklist**

- [ ] MongoDB secured with authentication
- [ ] Environment variables for sensitive data
- [ ] HTTPS enabled for API
- [ ] CORS configured for production domain
- [ ] Error handling and logging
- [ ] Resource monitoring (CPU, memory, disk)
- [ ] Backup strategy for database
- [ ] Rate limiting on API endpoints

### **Environment Variables**

Create `.env` file:
```bash
MONGO_URI=mongodb://localhost:27017
DB_NAME=engagement_db
FLASK_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com
```

### **MongoDB Production Setup**

```bash
# Enable authentication
mongod --auth --dbpath /data/db

# Create admin user
mongosh
use admin
db.createUser({
  user: "admin",
  pwd: "secure_password",
  roles: ["userAdminAnyDatabase", "readWriteAnyDatabase"]
})
```

### **Flask Production Server**

Use **Gunicorn** instead of development server:

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api.server:app
```

### **Systemd Service**

Create `/etc/systemd/system/annotation-backend.service`:

```ini
[Unit]
Description=Annotation App Backend API
After=network.target mongod.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/kira/personal/surja
Environment="PATH=/home/kira/personal/surja/venv_db/bin"
ExecStart=/home/kira/personal/surja/venv_db/bin/gunicorn -w 4 -b 0.0.0.0:5000 api.server:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable service:**
```bash
sudo systemctl enable annotation-backend
sudo systemctl start annotation-backend
sudo systemctl status annotation-backend
```

---

## Troubleshooting

### **Common Issues**

**1. MongoDB Connection Failed**
```
pymongo.errors.ServerSelectionTimeoutError
```
**Solution:**
```bash
# Check if MongoDB is running
ps aux | grep mongod

# Start MongoDB
mongod --dbpath /data/db --fork
```

**2. Model Files Not Found**
```
OSError: Unable to open file (file signature not found)
```
**Solution:**
```bash
# Verify model files exist in project root
ls -lh 3_pwindow_lstm_model*.h5

# Should see: 3_pwindow_lstm_model0.h5, 3_pwindow_lstm_model1.h5
```

**3. Port Already in Use**
```
OSError: [Errno 98] Address already in use
```
**Solution:**
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
kill -9 <PID>
```

**4. CORS Errors**
```
Access-Control-Allow-Origin header is missing
```
**Solution:** Ensure CORS is enabled in `api/server.py`:
```python
from flask_cors import CORS
CORS(app, origins=['http://localhost:5173'])
```

---

## Performance Optimization

### **Database Optimization**

**Indexes:**
```python
# Create compound indexes
db.predictions.createIndex({ user_id: 1, video_no: 1 })
db.signals.createIndex({ user_id: 1, timestamp: 1 })
```

**Query Optimization:**
```python
# Use projections to limit returned fields
predictions = collection.find(
    {'user_id': 'user1', 'video_no': 2},
    {'_id': 0, 'probe': 1, 'starttime': 1}
)
```

### **Bulk Operations**

**Batch inserts instead of single inserts:**
```python
# Bad: Single inserts
for signal in signals:
    insert_signal(signal)

# Good: Bulk insert
insert_signals_bulk(signals)
```

### **Caching**

**Cache frequently accessed data:**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_video_config(video_id):
    return video_configs[video_id]
```

---

## Resources

- **Flask Documentation:** https://flask.palletsprojects.com
- **PyMongo Documentation:** https://pymongo.readthedocs.io
- **MongoDB Manual:** https://docs.mongodb.com/manual/
- **Scikit-learn:** https://scikit-learn.org/stable/
- **TensorFlow:** https://www.tensorflow.org/guide
- **LSTM Tutorial:** https://colah.github.io/posts/2015-08-Understanding-LSTMs/

---

**Last Updated:** 2025-11-21  
**Version:** 2.0.0  
**Maintainer:** Development Team

