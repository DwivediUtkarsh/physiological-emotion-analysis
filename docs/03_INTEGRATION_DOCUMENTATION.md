# 🔗 Integration Documentation - Frontend ↔ Backend ↔ Database

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Communication Flow](#communication-flow)
4. [API Integration](#api-integration)
5. [Data Flow Examples](#data-flow-examples)
6. [User Session Management](#user-session-management)
7. [Real-time Updates](#real-time-updates)
8. [Error Handling](#error-handling)
9. [Security & CORS](#security--cors)
10. [Deployment Architecture](#deployment-architecture)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Annotation App consists of three main components that work together:

1. **Frontend (React)** - User interface for video annotation
2. **Backend (Flask + Python)** - Emotion analysis processing
3. **Database (MongoDB)** - Persistent data storage

This document explains how these components communicate and integrate.

---

## System Architecture

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    React Frontend                         │  │
│  │                (localhost:5173 - Dev)                     │  │
│  │                                                           │  │
│  │  - Video playback interface                              │  │
│  │  - Emotion prediction visualization                      │  │
│  │  - Manual annotation tools                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌──────────────────────┐              ┌──────────────────────┐
│   Flask Backend      │              │  FastAPI Backend     │
│   (localhost:5000)   │              │  (localhost:8000)    │
│                      │              │                      │
│  - Video session     │              │  - User auth         │
│  - Signal processing │              │  - Manual            │
│  - ML predictions    │              │    annotations       │
│  - API endpoints     │              │    (CSV storage)     │
└──────────┬───────────┘              └──────────────────────┘
           │
           │ PyMongo
           │
           ▼
┌──────────────────────────────────────┐
│         MongoDB                      │
│      (localhost:27017)               │
│                                      │
│  Collections:                        │
│  - signals (GSR, HR data)            │
│  - video_starts (session tracking)   │
│  - predictions (ML results)          │
│  - active_predictions (frontend)     │
│  - features (ML features)            │
│  - change_scores (analysis data)     │
└──────────────────────────────────────┘
```

### **Technology Stack Summary**

| Layer | Technology | Port | Purpose |
|-------|------------|------|---------|
| **Frontend** | React + TypeScript + Vite | 5173 | User interface |
| **Backend API** | Flask + Python | 5000 | Emotion analysis |
| **Annotations API** | FastAPI + Python | 8000 | Manual annotations |
| **Database** | MongoDB | 27017 | Data persistence |

---

## Communication Flow

### **Complete User Journey**

```
1. User Login
   Frontend (Login.tsx)
        │
        │ POST /login
        ▼
   FastAPI Backend (port 8000)
        │
        │ Returns JWT token
        ▼
   Frontend (stores in localStorage)


2. Video Playback & Processing
   Frontend (VideoAnnotation.tsx)
        │
        │ User clicks play
        ▼
   Frontend calls BackendAPI.startVideo()
        │
        │ POST /api/video/{video_id}/start
        │ Body: { video_id, timestamp, user_id, session_id }
        ▼
   Flask Backend (api/server.py)
        │
        │ Records video start
        ▼
   MongoDB (video_starts collection)
        │
        │ Triggers processing pipeline
        ▼
   Python Pipeline (main.py → signals.py → ML models)
        │
        │ Processes signals, runs ML models
        ▼
   MongoDB (predictions & active_predictions collections)


3. Real-time Prediction Display
   Frontend (polling every 5 seconds)
        │
        │ GET /api/predictions/video/{video_id}?user_id={user_id}
        ▼
   Flask Backend
        │
        │ Queries MongoDB
        ▼
   MongoDB (active_predictions collection)
        │
        │ Returns prediction segments
        ▼
   Flask Backend (formats response)
        │
        │ JSON response with segments
        ▼
   Frontend (SegmentedProgressBar.tsx)
        │
        │ Renders color-coded timeline
        ▼
   User sees real-time emotion predictions


4. Manual Annotation
   Frontend (AnnotationTimeline.tsx)
        │
        │ User clicks segment to annotate
        ▼
   Frontend calls annotations API
        │
        │ POST /annotations/{video_name}
        │ Body: { annotations array, mode }
        ▼
   FastAPI Backend (annotations-backend/)
        │
        │ Saves to CSV file
        ▼
   CSV File (annotations/{username}/{video_name}_{mode}.csv)
```

---

## API Integration

### **1. Backend API Client (Flask - Emotion Analysis)**

**File:** `frontend/src/lib/backend-api.ts`

**Base URL:** `http://localhost:5000`

#### **Configuration**

```typescript
const BACKEND_API_BASE = 
  import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:5000';
```

#### **API Methods**

**Start Video Processing**
```typescript
async startVideo(videoId: number, userId: string): Promise<void> {
  const timestamp = Date.now();
  const sessionId = `${userId}_${videoId}_${timestamp}`;
  
  await fetch(`${BACKEND_API_BASE}/api/video/${videoId}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_id: videoId,
      timestamp,
      user_id: userId,
      session_id: sessionId
    })
  });
}
```

**Backend Endpoint (Flask):**
```python
@video_session_bp.route('/start', methods=['POST'])
def start_video_session():
    data = request.get_json()
    video_id = data.get('video_id')
    user_id = data.get('user_id', 'anonymous')
    session_id = data.get('session_id')
    timestamp = data.get('timestamp', int(time.time() * 1000))
    
    # Record in MongoDB
    insert_video_start(timestamp, video_id, user_id, session_id)
    
    # Start processing pipeline
    trigger_backend_pipeline(video_id, timestamp, user_id, session_id)
    
    return jsonify({'success': True, 'session_id': session_id})
```

**Database Write (MongoDB):**
```python
def insert_video_start(timestamp, video_id, user_id, session_id):
    collection = get_collection('video_starts')
    document = {
        'timestamp': timestamp,
        'video_id': video_id,
        'user_id': user_id,
        'session_id': session_id,
        'created_at': datetime.now()
    }
    collection.insert_one(document)
```

---

**Get Video Predictions**
```typescript
async getVideoPredictions(
  videoId: number, 
  userId?: string
): Promise<PredictionSegment[]> {
  const url = new URL(`${BACKEND_API_BASE}/api/predictions/video/${videoId}`);
  
  if (userId) {
    url.searchParams.append('user_id', userId);
  }
  
  const response = await fetch(url.toString());
  const data = await response.json();
  
  return data.segments || [];
}
```

**Backend Endpoint (Flask):**
```python
@app.route('/api/predictions/video/<int:video_id>')
def get_predictions_by_video(video_id):
    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')
    
    # Query MongoDB with user filtering
    predictions = get_predictions_by_video_id(
        video_id, 
        user_id=user_id, 
        session_id=session_id
    )
    
    # Format as segments
    segments = []
    for i, pred in enumerate(predictions):
        segments.append({
            'segment_index': i,
            'timestamp': pred.get('starttime'),
            'probe': pred.get('probe'),
            'emotion': emotion_map[pred.get('probe')],
            'color': color_map[pred.get('probe')],
            'cluster_id': pred.get('cluster_id', 0)
        })
    
    return jsonify({
        'success': True,
        'video_id': video_id,
        'segments': segments,
        'total': len(segments)
    })
```

**Database Query (MongoDB):**
```python
def get_predictions_by_video_id(video_id, user_id=None, session_id=None):
    collection = get_collection('predictions')
    query = {'video_no': video_id}
    
    if user_id:
        query['user_id'] = user_id
    if session_id:
        query['session_id'] = session_id
    
    predictions = list(collection.find(query).sort('starttime', 1))
    return predictions
```

**Frontend Display:**
```typescript
// In VideoAnnotation.tsx
const [predictions, setPredictions] = useState<PredictionSegment[]>([]);

useEffect(() => {
  const loadPredictions = async () => {
    const userId = localStorage.getItem('username');
    const segments = await BackendAPI.getVideoPredictions(
      backendVideoId, 
      userId
    );
    setPredictions(segments);
  };
  
  loadPredictions();
}, [backendVideoId]);

// Render
<SegmentedProgressBar
  segments={predictions}
  currentTime={currentTime}
  duration={video.duration}
/>
```

---

**Polling for Real-time Updates**
```typescript
startPollingPredictions(
  videoId: number,
  onUpdate: (segments: PredictionSegment[]) => void,
  intervalMs: number = 5000
): () => void {
  const intervalId = setInterval(async () => {
    try {
      const userId = localStorage.getItem('username');
      const segments = await this.getVideoPredictions(videoId, userId);
      onUpdate(segments);
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, intervalMs);
  
  // Return stop function
  return () => clearInterval(intervalId);
}
```

**Frontend Usage:**
```typescript
// In VideoAnnotation.tsx
const [stopPolling, setStopPolling] = useState<(() => void) | null>(null);

const startPolling = () => {
  const stop = BackendAPI.startPollingPredictions(
    backendVideoId,
    (newSegments) => {
      setPredictions(newSegments);
    },
    5000 // Poll every 5 seconds
  );
  setStopPolling(() => stop);
};

const stopPollingFunc = () => {
  if (stopPolling) {
    stopPolling();
    setStopPolling(null);
  }
};

// Start polling when video plays
const handleVideoPlay = async () => {
  await BackendAPI.startVideo(backendVideoId, userId);
  startPolling();
};

// Stop polling when video pauses
const handleVideoPause = async () => {
  await BackendAPI.stopVideo(sessionId, backendVideoId);
  stopPollingFunc();
};
```

---

### **2. Annotations API Client (FastAPI - Manual Annotations)**

**Base URL:** `http://localhost:8000`

**Authentication**
```typescript
// Login
const response = await fetch('http://localhost:8000/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const data = await response.json();
localStorage.setItem('token', data.access_token);
localStorage.setItem('username', username);
```

**Save Annotations**
```typescript
const saveAnnotations = async (
  videoName: string,
  mode: string,
  annotations: VideoAnnotation[]
) => {
  const token = localStorage.getItem('token');
  
  await fetch(`http://localhost:8000/annotations/${videoName}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      annotations: annotations,
      mode: mode
    })
  });
};
```

**FastAPI Backend:**
```python
@app.post("/annotations/{video_name}")
async def save_annotations(
    video_name: str,
    data: dict,
    current_user: str = Depends(get_current_user)
):
    annotations = data.get('annotations', [])
    mode = data.get('mode', 'full')
    
    # Save to CSV
    filepath = f"annotations/{current_user}/{video_name}_{mode}.csv"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['segment', 'emotion', 'timestamp'])
        for ann in annotations:
            writer.writerow([
                ann['segment'],
                ann['emotion'],
                ann['timestamp']
            ])
    
    return {"success": True, "message": "Annotations saved"}
```

---

## Data Flow Examples

### **Example 1: Video Start & Prediction Flow**

**Step-by-Step:**

1. **Frontend initiates video playback**
```typescript
// VideoAnnotation.tsx
const handleVideoPlay = async () => {
  const userId = "user1";
  const videoId = 2;
  
  await BackendAPI.startVideo(videoId, userId);
  // Session ID generated: "user1_2_1732178316000"
};
```

2. **API call to Flask backend**
```http
POST http://localhost:5000/api/video/2/start
Content-Type: application/json

{
  "video_id": 2,
  "timestamp": 1732178316000,
  "user_id": "user1",
  "session_id": "user1_2_1732178316000"
}
```

3. **Backend records in MongoDB**
```python
# api/video_session_manager.py
insert_video_start(
    timestamp=1732178316000,
    video_id=2,
    user_id="user1",
    session_id="user1_2_1732178316000"
)
```

4. **MongoDB document created**
```javascript
// video_starts collection
{
  "_id": ObjectId("..."),
  "timestamp": 1732178316000,
  "video_id": 2,
  "user_id": "user1",
  "session_id": "user1_2_1732178316000",
  "created_at": ISODate("2025-11-21T11:53:36Z")
}
```

5. **Backend triggers processing pipeline**
```python
# Starts background thread
trigger_backend_pipeline(
    video_id=2,
    timestamp=1732178316000,
    user_id="user1",
    session_id="user1_2_1732178316000"
)
```

6. **Signal processing & ML prediction**
```python
# signals.py collects sensor data
signal_data = [
    {
        'time_series': 1,
        'gsr': 250,
        'hr': 70,
        'timestamp': 1732178316000,
        'datetime': '2025-11-21 11:53:36',
        'user_id': 'user1',
        'session_id': 'user1_2_1732178316000'
    },
    # ... more signals
]
insert_signals_bulk(signal_data)

# model_prediction.py runs ML models
get_model_prediction(
    test=features,
    nearest_centroid_index=1,
    starttime=1732178316000,
    v_no=2,
    user_id="user1",
    session_id="user1_2_1732178316000"
)
# Predicts: "HH" (Happy)
```

7. **Predictions stored in MongoDB**
```javascript
// predictions collection (permanent)
{
  "_id": ObjectId("..."),
  "starttime": 1732178316000,
  "video_no": 2,
  "probe": "HH",
  "cluster_id": 1,
  "user_id": "user1",
  "session_id": "user1_2_1732178316000",
  "created_at": ISODate("2025-11-21T11:53:36Z")
}

// active_predictions collection (for frontend, TTL 1 hour)
{
  "_id": ObjectId("..."),
  "starttime": 1732178316000,
  "video_no": 2,
  "probe": "HH",
  "user_id": "user1",
  "session_id": "user1_2_1732178316000",
  "created_at": ISODate("2025-11-21T11:53:36Z")
}
```

8. **Frontend polls for predictions**
```typescript
// Every 5 seconds
const segments = await BackendAPI.getVideoPredictions(2, "user1");
```

9. **Backend queries MongoDB & responds**
```http
GET http://localhost:5000/api/predictions/video/2?user_id=user1

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
    },
    // ... more segments
  ],
  "total": 30
}
```

10. **Frontend displays predictions**
```typescript
// SegmentedProgressBar.tsx
<div className="flex h-8 rounded overflow-hidden">
  {segments.map((segment, i) => (
    <div
      key={i}
      className="flex-1"
      style={{ backgroundColor: segment.color }}
      title={segment.emotion}
    />
  ))}
</div>
```

**User sees:** Color-coded timeline with emotions!

---

### **Example 2: User Separation in Action**

**Scenario:** Two users watching the same video simultaneously.

**User 1 Session:**
```typescript
// Frontend (User 1)
localStorage.setItem('username', 'user1');
await BackendAPI.startVideo(2, 'user1');
// session_id: "user1_2_1732178316000"
```

**User 2 Session:**
```typescript
// Frontend (User 2)
localStorage.setItem('username', 'user2');
await BackendAPI.startVideo(2, 'user2');
// session_id: "user2_2_1732178616000"
```

**MongoDB Data:**
```javascript
// video_starts collection
[
  {
    "video_id": 2,
    "user_id": "user1",
    "session_id": "user1_2_1732178316000",
    "timestamp": 1732178316000
  },
  {
    "video_id": 2,
    "user_id": "user2",
    "session_id": "user2_2_1732178616000",
    "timestamp": 1732178616000
  }
]

// predictions collection
[
  // User 1's predictions
  { "video_no": 2, "probe": "HH", "user_id": "user1", "starttime": 1732178316000 },
  { "video_no": 2, "probe": "HL", "user_id": "user1", "starttime": 1732178321000 },
  
  // User 2's predictions
  { "video_no": 2, "probe": "LL", "user_id": "user2", "starttime": 1732178616000 },
  { "video_no": 2, "probe": "LH", "user_id": "user2", "starttime": 1732178621000 },
]
```

**User 1 fetches predictions:**
```http
GET /api/predictions/video/2?user_id=user1

Returns: Only user1's predictions (HH, HL, ...)
```

**User 2 fetches predictions:**
```http
GET /api/predictions/video/2?user_id=user2

Returns: Only user2's predictions (LL, LH, ...)
```

**Result:** Complete data isolation between users!

---

## User Session Management

### **Session Lifecycle**

```
┌─────────────────────────────────────────────────────────┐
│                  Session Lifecycle                      │
└─────────────────────────────────────────────────────────┘

1. Login
   └─> Frontend: Store username & token in localStorage
   
2. Video Selection
   └─> Frontend: Navigate to /video/:videoId
   
3. Video Play
   ├─> Generate session_id: "{username}_{videoId}_{timestamp}"
   ├─> POST /api/video/{videoId}/start
   ├─> Backend: Record in video_starts collection
   └─> Backend: Start processing pipeline
   
4. During Playback
   ├─> Frontend: Poll for predictions every 5s
   ├─> Backend: Process signals → ML → MongoDB
   └─> Frontend: Update visualization
   
5. Video Pause/End
   ├─> POST /api/video/{videoId}/stop
   └─> Backend: Stop processing
   
6. Logout
   └─> Frontend: Clear localStorage
```

### **Session ID Format**

**Structure:** `{user_id}_{video_id}_{timestamp}`

**Examples:**
```
user1_2_1732178316000
user1_3_1732178916000
user2_2_1732179216000
```

**Benefits:**
- Unique identifier per viewing session
- Tracks multiple viewings of same video by same user
- Enables session-based analytics

### **Session Storage Locations**

| Data | Frontend Storage | Backend Storage | Database Storage |
|------|------------------|-----------------|------------------|
| Username | localStorage | - | video_starts.user_id |
| Token | localStorage | - | - |
| session_id | Runtime state | Runtime state | video_starts.session_id |
| Predictions | Runtime state (polling) | - | predictions.* |

---

## Real-time Updates

### **Polling Strategy**

**Current Implementation:** HTTP polling every 5 seconds

```typescript
// Frontend polling logic
const POLL_INTERVAL = 5000; // 5 seconds

const startPolling = () => {
  const intervalId = setInterval(async () => {
    const segments = await BackendAPI.getVideoPredictions(videoId, userId);
    setPredictions(segments);
  }, POLL_INTERVAL);
  
  return () => clearInterval(intervalId);
};
```

**When polling starts:**
- Video play event
- User navigates to video page

**When polling stops:**
- Video pause event
- Video end event
- User navigates away
- Component unmount

### **Why Polling?**

**Advantages:**
- ✅ Simple implementation
- ✅ No persistent connections
- ✅ Works with any server setup
- ✅ Easy to debug

**Disadvantages:**
- ❌ 5-second delay before updates appear
- ❌ Unnecessary requests if no new data
- ❌ Higher server load with many users

### **Future Enhancement: WebSockets**

**Planned Architecture:**
```typescript
// Frontend (WebSocket client)
const ws = new WebSocket('ws://localhost:5000/predictions');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    video_id: videoId,
    user_id: userId
  }));
};

ws.onmessage = (event) => {
  const newSegment = JSON.parse(event.data);
  setPredictions(prev => [...prev, newSegment]);
};
```

**Backend (WebSocket server):**
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('subscribe')
def handle_subscribe(data):
    room = f"{data['user_id']}_{data['video_id']}"
    join_room(room)

# When new prediction is generated
def on_new_prediction(user_id, video_id, segment):
    room = f"{user_id}_{video_id}"
    socketio.emit('new_prediction', segment, room=room)
```

**Benefits:**
- ⚡ Instant updates (< 100ms)
- 📉 Reduced server load
- 🔋 Lower bandwidth usage

---

## Error Handling

### **Frontend Error Handling**

**API Call Wrapper:**
```typescript
async function apiCall<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    
    // Show user-friendly error
    toast({
      title: "Connection Error",
      description: "Failed to connect to backend. Please try again.",
      variant: "destructive"
    });
    
    throw error;
  }
}
```

**Common Error Scenarios:**

**1. Backend Not Running**
```typescript
// Error: Failed to fetch
// Solution: Check if Flask API is running on port 5000

if (error.message.includes('Failed to fetch')) {
  toast({
    title: "Backend Unavailable",
    description: "Please ensure the backend server is running.",
  });
}
```

**2. MongoDB Connection Failed**
```python
# Backend error handling
try:
    predictions = get_predictions_by_video_id(video_id, user_id)
except pymongo.errors.ConnectionFailure:
    logger.error("MongoDB connection failed")
    return jsonify({
        'success': False,
        'error': 'Database unavailable'
    }), 503
```

**3. No Data Found**
```python
# Backend graceful response
predictions = get_predictions_by_video_id(video_id, user_id)

if not predictions:
    return jsonify({
        'success': True,
        'segments': [],
        'total': 0,
        'message': 'No predictions yet. Processing in progress...'
    })
```

**Frontend handles empty data:**
```typescript
if (segments.length === 0) {
  return (
    <div className="text-muted-foreground text-center p-4">
      No predictions yet. Analysis in progress...
    </div>
  );
}
```

### **Backend Error Logging**

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
try:
    result = process_data()
except Exception as e:
    logger.error(f"Processing failed: {e}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500
```

---

## Security & CORS

### **CORS Configuration**

**Backend (Flask):**
```python
from flask_cors import CORS

app = Flask(__name__)

# Development
CORS(app, origins=['http://localhost:5173'])

# Production
CORS(app, origins=[
    'https://yourdomain.com',
    'https://app.yourdomain.com'
])
```

**CORS Headers:**
```python
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response
```

### **Authentication Flow**

**JWT Token:**
```typescript
// Frontend stores token
const token = response.data.access_token;
localStorage.setItem('token', token);

// Include in API calls
fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

**Backend validates token:**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### **Data Validation**

**Frontend:**
```typescript
// Validate before sending
const validateVideoId = (id: number): boolean => {
  return id >= 1 && id <= 4 && Number.isInteger(id);
};

if (!validateVideoId(videoId)) {
  toast({ title: "Invalid video ID", variant: "destructive" });
  return;
}
```

**Backend:**
```python
from pydantic import BaseModel, validator

class VideoStartRequest(BaseModel):
    video_id: int
    user_id: str
    timestamp: int
    
    @validator('video_id')
    def validate_video_id(cls, v):
        if v < 1 or v > 4:
            raise ValueError('Invalid video ID')
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Invalid user ID')
        return v
```

---

## Deployment Architecture

### **Production Setup**

```
┌────────────────────────────────────────────────────────┐
│                     INTERNET                           │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│              Nginx Reverse Proxy                       │
│              (SSL Termination)                         │
└────────────────────────────────────────────────────────┘
                        │
          ┌─────────────┴──────────────┐
          │                            │
          ▼                            ▼
┌──────────────────┐        ┌──────────────────┐
│  Static Files    │        │   API Gateway    │
│  (React Build)   │        │   (Port 443)     │
│  CDN / S3        │        └──────────────────┘
└──────────────────┘                 │
                         ┌───────────┴───────────┐
                         │                       │
                         ▼                       ▼
              ┌──────────────────┐   ┌──────────────────┐
              │  Flask Backend   │   │ FastAPI Backend  │
              │  (Gunicorn)      │   │  (Uvicorn)       │
              │  Port 5000       │   │  Port 8000       │
              └──────────────────┘   └──────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   MongoDB Cluster    │
              │   (Replica Set)      │
              └──────────────────────┘
```

### **Environment Variables**

**Frontend (.env):**
```env
VITE_BACKEND_API_URL=https://api.yourdomain.com
VITE_ANNOTATIONS_API_URL=https://annotations.yourdomain.com
```

**Backend (.env):**
```env
MONGO_URI=mongodb://username:password@mongodb-host:27017/engagement_db?authSource=admin
DB_NAME=engagement_db
FLASK_SECRET_KEY=your-secure-random-key-here
CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

### **Docker Compose (Optional)**

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: secure_password

  backend:
    build: ./backend
    ports:
      - "5000:5000"
    depends_on:
      - mongodb
    environment:
      MONGO_URI: mongodb://admin:secure_password@mongodb:27017
      DB_NAME: engagement_db

  annotations:
    build: ./frontend/annotations-backend
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
      - annotations

volumes:
  mongodb_data:
```

---

## Troubleshooting

### **Common Integration Issues**

**1. CORS Errors**
```
Access to fetch at 'http://localhost:5000' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solutions:**
```python
# Backend: Ensure CORS is enabled
from flask_cors import CORS
CORS(app, origins=['http://localhost:5173'])

# Or allow all origins (dev only!)
CORS(app, origins='*')
```

**2. Predictions Not Showing**
```
Empty predictions array returned
```

**Debug Steps:**
```bash
# 1. Check if MongoDB has data
python scripts/verify_mongodb.py --users

# 2. Check API endpoint directly
curl http://localhost:5000/api/predictions/video/2?user_id=user1

# 3. Check browser console for errors
# Open DevTools → Console

# 4. Check backend logs
tail -f logs/backend.log
```

**3. Video Session Not Starting**
```
POST /api/video/2/start returns 500 error
```

**Debug:**
```python
# Check backend logs
logger.error(f"Video start failed: {e}")

# Common causes:
# - MongoDB not running
# - Invalid video_id
# - Missing user_id
# - Processing pipeline crash
```

**4. Polling Not Working**
```
Predictions frozen, not updating
```

**Check:**
```typescript
// In VideoAnnotation.tsx
console.log('Polling active:', !!stopPolling);
console.log('Video ID:', backendVideoId);
console.log('User ID:', userId);

// Check if polling is actually running
const stopPolling = BackendAPI.startPollingPredictions(
  videoId,
  (segments) => {
    console.log('Received segments:', segments.length);
    setPredictions(segments);
  }
);
```

### **Debug Tools**

**Browser DevTools:**
```javascript
// Check localStorage
console.log('User:', localStorage.getItem('username'));
console.log('Token:', localStorage.getItem('token'));

// Monitor network requests
// DevTools → Network → Filter: "predictions"
```

**Backend Debug Mode:**
```python
# api/server.py
app.config['DEBUG'] = True
app.run(debug=True)
```

**MongoDB Debug:**
```bash
mongosh engagement_db

# Check data
db.predictions.find({user_id: "user1", video_no: 2}).pretty()

# Count documents
db.predictions.countDocuments({user_id: "user1"})

# Check indexes
db.predictions.getIndexes()
```

---

## Performance Monitoring

### **Frontend Performance**

**Metrics to track:**
- API response time
- Prediction update latency
- Video buffering
- Component render time

**Implementation:**
```typescript
const measureAPIPerformance = async () => {
  const start = performance.now();
  await BackendAPI.getVideoPredictions(videoId, userId);
  const end = performance.now();
  
  console.log(`API call took ${end - start}ms`);
};
```

### **Backend Performance**

**Metrics to track:**
- Request processing time
- MongoDB query time
- ML inference time
- Memory usage

**Implementation:**
```python
import time

@app.route('/api/predictions/video/<int:video_id>')
def get_predictions_by_video(video_id):
    start_time = time.time()
    
    # Process request
    predictions = get_predictions_by_video_id(video_id)
    
    elapsed = time.time() - start_time
    logger.info(f"Request processed in {elapsed:.3f}s")
    
    return jsonify(predictions)
```

---

## Summary

### **Key Integration Points**

1. ✅ **Frontend → Backend API**
   - REST endpoints for video session management
   - Polling for real-time predictions
   - User-specific data filtering

2. ✅ **Backend → MongoDB**
   - PyMongo for database operations
   - User separation with `user_id` and `session_id`
   - Bulk operations for performance

3. ✅ **Backend → ML Pipeline**
   - Signal processing
   - Feature extraction
   - LSTM-based emotion prediction

4. ✅ **Frontend → Annotations API**
   - JWT authentication
   - Manual annotation storage
   - CSV-based persistence

### **Data Flow Summary**

```
User Action → Frontend → Backend API → MongoDB → Backend Pipeline → 
ML Models → MongoDB → Backend API → Frontend → Visual Display
```

### **Best Practices**

- ✅ Always include `user_id` in requests
- ✅ Generate unique `session_id` per viewing
- ✅ Handle errors gracefully
- ✅ Use polling for real-time updates (upgrade to WebSockets later)
- ✅ Validate data on both frontend and backend
- ✅ Monitor performance metrics
- ✅ Log errors for debugging

---

**Last Updated:** 2025-11-21  
**Version:** 2.0.0  
**Maintainer:** Development Team

