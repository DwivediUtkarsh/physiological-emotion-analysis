# 📱 Frontend Documentation - Annotation App

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Key Features](#key-features)
5. [Components](#components)
6. [Pages](#pages)
7. [Configuration](#configuration)
8. [API Integration](#api-integration)
9. [State Management](#state-management)
10. [Development Guide](#development-guide)
11. [Deployment](#deployment)

---

## Overview

The Annotation App frontend is a modern React-based web application designed for emotion annotation and visualization during video playback. It provides a user-friendly interface for researchers and participants to:

- Watch videos in three different modes (Full A/V, Video Only, Audio Only)
- View automatic emotion predictions as colored timeline segments
- Manually annotate emotions for research validation
- Track real-time physiological signal analysis results

**Location:** `/home/kira/personal/surja/frontend/`

**Purpose:** Multi-modal video annotation interface with automatic emotion prediction visualization

---

## Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI framework |
| **TypeScript** | 5.x | Type safety |
| **Vite** | 5.x | Build tool & dev server |
| **React Router** | 6.x | Client-side routing |
| **TanStack Query** | Latest | Server state management |

### UI Libraries

| Library | Purpose |
|---------|---------|
| **ShadCN UI** | Pre-built accessible components |
| **Tailwind CSS** | Utility-first styling |
| **Lucide React** | Icon library |
| **Radix UI** | Headless UI primitives |

### Development Tools

- **ESLint** - Code linting
- **TypeScript** - Type checking
- **Vite** - Hot module replacement
- **Bun** - Package manager (alternative to npm)

---

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # ShadCN UI components
│   │   └── video/          # Video-specific components
│   │       ├── video-player.tsx
│   │       ├── annotation-timeline.tsx
│   │       └── SegmentedProgressBar.tsx
│   ├── pages/              # Page components (routes)
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── VideoLibrary.tsx
│   │   └── VideoAnnotation.tsx
│   ├── lib/                # Utility functions & API clients
│   │   ├── backend-api.ts  # Backend API client
│   │   └── utils.ts        # Helper functions
│   ├── config/             # Configuration files
│   │   └── videos.ts       # Video metadata configuration
│   ├── types/              # TypeScript type definitions
│   │   └── video.ts
│   ├── hooks/              # Custom React hooks
│   │   └── use-toast.ts
│   ├── App.tsx             # Main application component
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── annotations-backend/    # FastAPI backend for manual annotations
│   ├── annotations/        # User annotation storage (CSV)
│   ├── app_fastapi.py      # FastAPI server
│   └── requirements.txt
├── public/                 # Static assets
│   └── assets/
│       └── videos/         # Video files
├── package.json            # Dependencies
├── vite.config.ts          # Vite configuration
├── tailwind.config.ts      # Tailwind CSS configuration
└── tsconfig.json           # TypeScript configuration
```

---

## Key Features

### 1. **User Authentication**
- Login system with username/password
- JWT token-based authentication
- User session management via localStorage

### 2. **Video Library**
- Browse available videos
- Video metadata display (title, duration, description)
- Quick access to annotation interface

### 3. **Multi-Mode Video Playback**
Three distinct viewing modes for research purposes:
- **Full A/V** - Complete audio and video
- **Video Only** - Muted video playback
- **Audio Only** - Audio with black screen

### 4. **Automatic Emotion Prediction**
- Real-time emotion analysis from physiological signals
- Color-coded timeline segments (5-second intervals)
- Emotion labels: Happy (HH), Neutral (HL), Angry (LH), Sad (LL)

### 5. **Manual Annotation Interface**
- Click-to-annotate timeline
- Four emotion categories: Happy, Sad, Angry, Neutral
- Separate annotations per viewing mode
- Save/reset functionality

### 6. **Real-time Visualization**
- `SegmentedProgressBar` component shows predictions
- Color-coded emotion segments
- Current emotion indicator
- Synchronized with video playback

---

## Components

### Core UI Components (ShadCN)

Located in: `src/components/ui/`

- **Button** - Customizable button component
- **Card** - Content container with header/footer
- **Tabs** - Tabbed interface component
- **Alert** - Alert/notification messages
- **AlertDialog** - Confirmation dialogs
- **Toast** - Toast notifications

### Video Components

#### **VideoPlayer** (`src/components/video/video-player.tsx`)

Custom video player with enhanced controls.

**Props:**
```typescript
interface VideoPlayerProps {
  src: string;              // Video source URL
  onTimeUpdate: (time: number) => void;  // Time update callback
  onEnded?: () => void;     // Video ended callback
  onPlay?: () => void;      // Play callback
  onPause?: () => void;     // Pause callback
  className?: string;       // Additional CSS classes
  forceMuted?: boolean;     // Force muted state
  hideVideo?: boolean;      // Hide video (audio only mode)
}
```

**Features:**
- Custom play/pause controls
- Progress bar
- Time display
- Fullscreen support
- Keyboard shortcuts

**Usage:**
```typescript
<VideoPlayer
  src="/assets/videos/1.mp4"
  onTimeUpdate={(time) => setCurrentTime(time)}
  onPlay={handlePlay}
  onPause={handlePause}
  onEnded={handleEnd}
/>
```

#### **SegmentedProgressBar** (`src/components/video/SegmentedProgressBar.tsx`)

Displays emotion predictions as colored segments.

**Props:**
```typescript
interface SegmentedProgressBarProps {
  segments: Array<{
    color: string;      // Hex color code
    emotion: string;    // Emotion label
    probe: string;      // Probe code (HH/HL/LH/LL)
    timestamp: number;  // Segment timestamp
  }>;
  currentTime: number;  // Current video time
  duration: number;     // Total video duration
  className?: string;
  showLegend?: boolean; // Show current emotion label
}
```

**Features:**
- 5-second segment visualization
- Color-coded emotions
- Current segment highlighting
- Hover tooltips
- Progress indication

**Color Mapping:**
```typescript
HH (Happy):   #eecdac  // Beige
HL (Neutral): #7fc087  // Green
LH (Angry):   #f4978e  // Pink
LL (Sad):     #879af0  // Blue
```

**Usage:**
```typescript
<SegmentedProgressBar
  segments={predictions}
  currentTime={currentTime}
  duration={video.duration}
  showLegend={true}
/>
```

#### **AnnotationTimeline** (`src/components/video/annotation-timeline.tsx`)

Manual annotation interface.

**Props:**
```typescript
interface AnnotationTimelineProps {
  annotations: VideoAnnotation[];
  duration: number;
  currentTime: number;
  onAnnotationChange: (index: number, emotion: Emotion) => void;
}
```

**Features:**
- Click to change emotion
- Visual emotion indicators
- Current position marker
- Segment boundaries

---

## Pages

### **Login Page** (`src/pages/Login.tsx`)

**Route:** `/login`

**Features:**
- Username/password input
- Form validation
- JWT token storage
- Redirect to dashboard on success

**Authentication Flow:**
```
1. User enters credentials
2. POST to annotations backend (port 8000)
3. Receive JWT token
4. Store token + username in localStorage
5. Redirect to /dashboard
```

### **Dashboard** (`src/pages/Dashboard.tsx`)

**Route:** `/dashboard`

**Features:**
- Welcome message
- Quick stats (videos watched, annotations made)
- Navigation to video library
- User profile info

### **Video Library** (`src/pages/VideoLibrary.tsx`)

**Route:** `/video-library`

**Features:**
- Grid display of available videos
- Video cards with metadata
- Search/filter functionality
- Click to open annotation interface

**Video Metadata:**
```typescript
interface Video {
  id: string;          // Frontend video ID (e.g., "video1")
  name: string;        // Display name
  duration: number;    // Duration in seconds
  path: string;        // Video file path
  description?: string;
  thumbnail?: string;
}
```

### **Video Annotation** (`src/pages/VideoAnnotation.tsx`)

**Route:** `/video/:videoId`

**Main annotation interface with three modes.**

**Features:**
1. **Three-Mode Tabbed Interface**
   - Full A/V
   - Video Only (muted)
   - Audio Only (no video)

2. **Automatic Predictions Display**
   - Fetches predictions from MongoDB via API
   - Real-time polling for new predictions
   - Color-coded segmented timeline

3. **Manual Annotations**
   - Independent annotations per mode
   - Click-to-annotate interface
   - Save to CSV via FastAPI backend

4. **Video Session Management**
   - Start processing on play
   - Stop processing on pause/end
   - Session tracking with `session_id`

**State Management:**
```typescript
// User context
const userId = localStorage.getItem('username');
const backendVideoId = getBackendVideoId(videoId); // Map frontend to backend ID

// Predictions (from MongoDB)
const [predictions, setPredictions] = useState<PredictionSegment[]>([]);

// Manual annotations (separate per mode)
const [annotationsFull, setAnnotationsFull] = useState<VideoAnnotation[]>([]);
const [annotationsVideoOnly, setAnnotationsVideoOnly] = useState<VideoAnnotation[]>([]);
const [annotationsAudioOnly, setAnnotationsAudioOnly] = useState<VideoAnnotation[]>([]);

// Video state
const [currentTime, setCurrentTime] = useState(0);
const [isPlaying, setIsPlaying] = useState(false);
```

**Lifecycle:**
```
1. Load video metadata
2. Fetch existing predictions (MongoDB)
3. Fetch existing manual annotations (CSV)
4. User plays video → Start backend processing
5. Poll for new predictions every 5 seconds
6. Display predictions on segmented timeline
7. User manually annotates → Save to CSV
8. Video ends → Stop processing
```

---

## Configuration

### **Video Configuration** (`src/config/videos.ts`)

Maps frontend video IDs to backend numeric IDs.

```typescript
export interface VideoConfig {
  id: string;           // Frontend ID (e.g., "video1")
  backendId: number;    // Backend numeric ID (e.g., 1)
  name: string;         // Display name
  duration: number;     // Duration in seconds
  path: string;         // Video file path
  thumbnail?: string;
}

export const VIDEO_CONFIGS: VideoConfig[] = [
  {
    id: "video1",
    backendId: 1,
    name: "Baseline Video 1",
    duration: 180,
    path: "/assets/videos/0.mp4",
  },
  {
    id: "video2",
    backendId: 2,
    name: "Emotional Stimulus 1",
    duration: 151,
    path: "/assets/videos/1.mp4",
  },
  // ... more videos
];

// Helper functions
export const getBackendVideoId = (frontendId: string): number | undefined => {
  return VIDEO_CONFIGS.find(v => v.id === frontendId)?.backendId;
};
```

### **Environment Variables**

Create `.env` file in frontend root:

```env
# Backend API (MongoDB predictions)
VITE_BACKEND_API_URL=http://localhost:5000

# Annotations API (Manual annotations)
VITE_ANNOTATIONS_API_URL=http://localhost:8000
```

---

## API Integration

### **Backend API Client** (`src/lib/backend-api.ts`)

TypeScript client for emotion analysis backend.

**Base URL:** `http://localhost:5000`

#### **API Methods**

**1. Start Video Processing**
```typescript
await BackendAPI.startVideo(videoId: number, userId: string)
```
Notifies backend to begin emotion analysis.

**2. Stop Video Processing**
```typescript
await BackendAPI.stopVideo(sessionId: string, videoId: number)
```
Stops backend processing.

**3. Get Video Predictions**
```typescript
const segments = await BackendAPI.getVideoPredictions(
  videoId: number, 
  userId?: string
)
```
Fetches all prediction segments for a video.

**Response:**
```typescript
interface PredictionSegment {
  segment_index: number;
  timestamp: number;
  probe: 'HH' | 'HL' | 'LH' | 'LL';
  emotion: 'Happy' | 'Neutral' | 'Angry' | 'Sad';
  color: string;
  cluster_id?: number;
}
```

**4. Poll for Active Predictions**
```typescript
const stopPolling = BackendAPI.startPollingPredictions(
  videoId: number,
  onUpdate: (segments: PredictionSegment[]) => void,
  intervalMs: number = 5000
)
```
Continuously polls for new predictions. Returns stop function.

**5. Health Check**
```typescript
const isHealthy = await BackendAPI.isHealthy()
```

### **Annotations API Client**

**Base URL:** `http://localhost:8000`

Built-in to `VideoAnnotation.tsx` component.

**Endpoints:**
- `GET /annotations/{video_name}?mode={mode}` - Fetch annotations
- `POST /annotations/{video_name}` - Save annotations
- `POST /login` - User authentication
- `POST /register` - User registration

---

## State Management

### **Local State (useState)**

Used for component-specific state:
- Video playback state (currentTime, isPlaying)
- Annotations for each mode
- UI state (loading, errors)

### **Local Storage**

Persistent browser storage:
- `username` - Current user's username
- `token` - JWT authentication token

**Usage:**
```typescript
// Store
localStorage.setItem('username', username);
localStorage.setItem('token', token);

// Retrieve
const username = localStorage.getItem('username');
const token = localStorage.getItem('token');

// Clear (logout)
localStorage.removeItem('username');
localStorage.removeItem('token');
```

### **Server State (Future: TanStack Query)**

Currently using manual fetch, but can be enhanced with:
```typescript
import { useQuery } from '@tanstack/react-query';

const { data: predictions } = useQuery({
  queryKey: ['predictions', videoId, userId],
  queryFn: () => BackendAPI.getVideoPredictions(videoId, userId),
  refetchInterval: 5000, // Poll every 5 seconds
});
```

---

## Development Guide

### **Setup**

```bash
cd /home/kira/personal/surja/frontend

# Install dependencies
npm install
# or
bun install

# Start dev server
npm run dev
# or
bun run dev

# Access at http://localhost:5173
```

### **Build**

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### **Project Scripts**

```json
{
  "dev": "vite",                    // Start dev server
  "build": "tsc && vite build",     // Production build
  "preview": "vite preview",        // Preview build
  "lint": "eslint ."                // Run linter
}
```

### **Adding a New Video**

1. Add video file to `public/assets/videos/`
2. Update `src/config/videos.ts`:

```typescript
{
  id: "video5",
  backendId: 5,
  name: "New Video",
  duration: 120, // seconds
  path: "/assets/videos/new_video.mp4",
}
```

3. Update backend `video_durations` in `api/server.py`

### **Creating a New Component**

```bash
# Using ShadCN CLI
npx shadcn-ui@latest add [component-name]

# Example: Add dialog component
npx shadcn-ui@latest add dialog
```

### **Code Style**

- **TypeScript** for all new components
- **Functional components** with hooks
- **Tailwind CSS** for styling
- **Props interfaces** for type safety
- **ESLint** for code quality

**Example Component:**
```typescript
import React from 'react';
import { cn } from '@/lib/utils';

interface MyComponentProps {
  title: string;
  onClick?: () => void;
  className?: string;
}

export function MyComponent({ title, onClick, className }: MyComponentProps) {
  return (
    <div className={cn("p-4 rounded-lg", className)} onClick={onClick}>
      <h2 className="text-lg font-bold">{title}</h2>
    </div>
  );
}
```

---

## Deployment

### **Production Build**

```bash
npm run build
```

Output: `dist/` directory

### **Static Hosting**

Deploy `dist/` folder to:
- **Netlify**
- **Vercel**
- **GitHub Pages**
- **AWS S3 + CloudFront**

### **Environment Configuration**

Set environment variables in hosting platform:
```
VITE_BACKEND_API_URL=https://api.yourbackend.com
VITE_ANNOTATIONS_API_URL=https://annotations.yourbackend.com
```

### **Backend Requirements**

Ensure backend APIs are:
- ✅ Running and accessible
- ✅ CORS enabled for frontend domain
- ✅ HTTPS enabled in production
- ✅ Proper authentication configured

---

## Troubleshooting

### **Common Issues**

**1. CORS Errors**
```
Access to fetch at 'http://localhost:5000' has been blocked by CORS
```
**Solution:** Ensure Flask backend has CORS enabled:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

**2. Video Not Loading**
```
Failed to load video: 404 Not Found
```
**Solution:** Check video path in `videos.ts` matches actual file location in `public/assets/videos/`

**3. Predictions Not Showing**
```
No predictions displayed on timeline
```
**Solution:** 
- Check backend API is running
- Verify MongoDB has data: `python scripts/verify_mongodb.py --users`
- Check browser console for API errors

**4. Authentication Failed**
```
401 Unauthorized
```
**Solution:**
- Clear localStorage: `localStorage.clear()`
- Re-login
- Check token expiration in annotations backend

---

## Future Enhancements

### **Planned Features**

1. **Real-time Updates**
   - WebSocket connection for live predictions
   - No polling delay

2. **User Management**
   - Admin dashboard
   - User roles and permissions
   - Annotation review workflow

3. **Advanced Analytics**
   - Emotion statistics dashboard
   - Comparison across users
   - Export to CSV/PDF

4. **Accessibility**
   - Keyboard navigation
   - Screen reader support
   - High contrast mode

5. **Offline Support**
   - Service worker for caching
   - Offline annotation capability
   - Sync when online

---

## Resources

- **React Documentation:** https://react.dev
- **TypeScript Handbook:** https://www.typescriptlang.org/docs/
- **Vite Guide:** https://vitejs.dev/guide/
- **TailwindCSS:** https://tailwindcss.com/docs
- **ShadCN UI:** https://ui.shadcn.com
- **React Router:** https://reactrouter.com

---

**Last Updated:** 2025-11-21  
**Version:** 2.0.0  
**Maintainer:** Development Team

