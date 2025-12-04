from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import os
import csv
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Literal
from collections import defaultdict

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
ANNOTATIONS_DIR = os.path.join(os.path.dirname(__file__), 'annotations')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# Secret key for JWT tokens - in production, use environment variable
SECRET_KEY = "your-secret-key-keep-it-safe"
ALGORITHM = "HS256"

# Load users from JSON file
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save users to JSON file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Load initial users
users_db = load_users()

# Annotation mode type
AnnotationMode = Literal['full', 'video_only', 'audio_only']

class User(BaseModel):
    username: str
    is_admin: bool = False

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AnnotationRequest(BaseModel):
    video_name: str
    duration: int
    annotations: list[int]  # 0: Happy, 1: Sad, 2: Angry, 3: Neutral
    mode: AnnotationMode = 'full'

class UserStats(BaseModel):
    total_annotations: int
    emotion_distribution: Dict[str, int]
    videos_annotated: List[str]
    last_active: Optional[str]
    completion_rate: float

class VideoStats(BaseModel):
    total_segments: int
    annotated_segments: int
    completion_percentage: float
    emotion_distribution: Dict[str, int]
    annotated_by_users: List[str]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Reload users to get latest data
        users_db = load_users()
        user_data = users_db.get(username)
        
        if user_data is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user_data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.post("/signup")
def signup(user: UserCreate):
    # Reload users to get latest data
    users_db = load_users()
    
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user directory for annotations
    user_dir = os.path.join(ANNOTATIONS_DIR, user.username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Add user to database
    users_db[user.username] = {
        "username": user.username,
        "password": user.password,
        "is_admin": False
    }
    
    # Save updated users
    save_users(users_db)
    
    # Create and return token
    access_token = create_access_token({"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Reload users to get latest data
    users_db = load_users()
    
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token({"sub": user["username"]})
    return Token(access_token=access_token, token_type="bearer")

def get_user_annotations_dir(username: str) -> str:
    user_dir = os.path.join(ANNOTATIONS_DIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def get_mode_csv_path(username: str, video_name: str, mode: AnnotationMode) -> str:
    """Get the CSV file path for a specific user, video, and annotation mode.
    
    For 'full' mode, falls back to legacy naming if the mode-specific file doesn't exist.
    """
    user_dir = get_user_annotations_dir(username)
    
    # Preferred path with mode suffix
    preferred_path = os.path.join(user_dir, f"{video_name}.{mode}.csv")
    
    # For 'full' mode, check legacy path if preferred doesn't exist
    if mode == 'full':
        legacy_path = os.path.join(user_dir, f"{video_name}.csv")
        if os.path.exists(legacy_path) and not os.path.exists(preferred_path):
            return legacy_path
    
    return preferred_path

@app.get("/admin/detailed-stats")
def get_detailed_stats(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin users can access statistics")
    
    # Reload users to get latest data
    users_db = load_users()
    
    # Initialize statistics
    user_stats = {}
    video_stats = {}
    overall_emotion_distribution = defaultdict(int)
    
    # Emotion mapping
    emotion_map = {0: "Happy", 1: "Sad", 2: "Angry", 3: "Neutral"}
    
    # Process all annotations
    for username in users_db.keys():
        if username == "admin":  # Skip admin user
            continue
            
        user_dir = get_user_annotations_dir(username)
        if not os.path.exists(user_dir):
            continue
            
        # Initialize user statistics
        user_emotion_dist = defaultdict(int)
        user_videos = []
        last_active = None
        total_segments = 0
        annotated_segments = 0
        
        # Process each annotation file
        for csv_file in os.listdir(user_dir):
            if not csv_file.endswith('.csv'):
                continue
                
            video_name = csv_file.replace('.csv', '')
            csv_path = os.path.join(user_dir, csv_file)
            file_stat = os.stat(csv_path)
            file_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Update last active time
            if last_active is None or file_modified > last_active:
                last_active = file_modified
            
            # Read annotations
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) == 2 and row[1].isdigit():
                        emotion_idx = int(row[1])
                        emotion = emotion_map[emotion_idx]
                        user_emotion_dist[emotion] += 1
                        overall_emotion_distribution[emotion] += 1
                        total_segments += 1
                        if emotion_idx != 3:  # Not Neutral
                            annotated_segments += 1
            
            user_videos.append(video_name)
            
            # Update video statistics
            if video_name not in video_stats:
                video_stats[video_name] = {
                    "total_segments": total_segments,
                    "annotated_segments": annotated_segments,
                    "completion_percentage": (annotated_segments / total_segments * 100) if total_segments > 0 else 0,
                    "emotion_distribution": dict(user_emotion_dist),
                    "annotated_by_users": [username]
                }
            else:
                video_stats[video_name]["annotated_by_users"].append(username)
                video_stats[video_name]["emotion_distribution"].update(dict(user_emotion_dist))
        
        # Calculate user completion rate
        completion_rate = (annotated_segments / total_segments * 100) if total_segments > 0 else 0
        
        # Store user statistics
        user_stats[username] = {
            "total_annotations": total_segments,
            "emotion_distribution": dict(user_emotion_dist),
            "videos_annotated": user_videos,
            "last_active": last_active,
            "completion_rate": completion_rate
        }
    
    return {
        "user_statistics": user_stats,
        "video_statistics": video_stats,
        "overall_emotion_distribution": dict(overall_emotion_distribution),
        "total_users": len(user_stats),
        "total_videos_annotated": len(video_stats)
    }

@app.get("/annotations/{video_name}")
def get_annotations(video_name: str, duration: int, mode: AnnotationMode = 'full', current_user: User = Depends(get_current_user)):
    # Reload users to get latest data
    users_db = load_users()
    
    if current_user.is_admin:
        # Admin can access all user annotations
        all_annotations = {}
        for username in users_db.keys():
            user_csv_path = get_mode_csv_path(username, video_name, mode)
            if os.path.exists(user_csv_path):
                all_annotations[username] = read_user_annotations(user_csv_path, duration)
        return {"annotations": all_annotations}
    else:
        # Regular users can only access their own annotations
        user_csv_path = get_mode_csv_path(current_user.username, video_name, mode)
        annotations = read_user_annotations(user_csv_path, duration)
        return {"annotations": annotations}

def read_user_annotations(csv_path: str, duration: int) -> List[int]:
    num_segments = (duration + 4) // 5
    annotations = [3] * num_segments  # Default: Neutral
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for i, row in enumerate(reader):
                # Support both old format (2 columns) and new format (3 columns)
                if len(row) >= 2 and row[1].isdigit():
                    annotations[i] = int(row[1])
    return annotations

@app.post("/annotations/{video_name}")
def save_annotations(video_name: str, req: AnnotationRequest, current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin users cannot save annotations")
    
    user_csv_path = get_mode_csv_path(current_user.username, video_name, req.mode)
    with open(user_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["segment number", "annotation", "mode"])
        for i, val in enumerate(req.annotations):
            writer.writerow([i, val, req.mode])
    return {"status": "success"}