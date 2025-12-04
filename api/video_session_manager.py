"""
Video Session Manager API
Handles video playback events from frontend and triggers emotion analysis pipeline.

This module ports the full processing logic from main.py into API-triggered functions,
including:
- Signal extraction from signals_data.csv
- Change point score calculation
- Baseline extraction and physiological difference calculation
- Feature generation for LSTM model
- Model prediction with proper input shape

Author: Backend Team
Date: 2024
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, Any, List
from flask import Blueprint, request, jsonify

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database functions
try:
    from db_models import insert_video_start, clear_active_predictions
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    print(f"⚠️  Database models not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask blueprint
video_session_bp = Blueprint('video_session', __name__)

# Video duration mapping (milliseconds) - matches existing system
VIDEO_DURATIONS = {
    1: 180000,  # Video 1: 180 seconds (3 minutes)
    2: 151000,  # Video 2: 151 seconds (~2.5 minutes)
    3: 160000,  # Video 3: 160 seconds (~2.7 minutes)
    4: 117000   # Video 4: 117 seconds (~2 minutes)
}

# Video valence/arousal mapping (from cal_physiological_diff.py)
VIDEO_VALENCE_AROUSAL = {
    1: (1, 1),  # High valence, High arousal
    2: (0, 1),  # Low valence, High arousal
    3: (0, 0),  # Low valence, Low arousal
    4: (1, 0),  # High valence, Low arousal
}

# Track active processing sessions
_active_sessions: Dict[str, Dict[str, Any]] = {}
_session_lock = threading.Lock()

# Global cluster index (set after first video for user profiling)
_user_cluster_indices: Dict[str, int] = {}


class VideoSessionManager:
    """
    Manages video processing sessions.
    Coordinates between frontend requests and backend processing pipeline.
    """
    
    @staticmethod
    def create_session(video_id: int, timestamp: int, user_id: str, session_id: str) -> Dict[str, Any]:
        """Create a new video processing session."""
        session_info = {
            'video_id': video_id,
            'timestamp': timestamp,
            'user_id': user_id,
            'session_id': session_id,
            'start_time': datetime.now(),
            'status': 'initializing',
            'error': None
        }
        
        with _session_lock:
            _active_sessions[session_id] = session_info
        
        logger.info(f"Created session: {session_id} for video {video_id}")
        return session_info
    
    @staticmethod
    def update_session_status(session_id: str, status: str, error: Optional[str] = None):
        """Update session status."""
        with _session_lock:
            if session_id in _active_sessions:
                _active_sessions[session_id]['status'] = status
                if error:
                    _active_sessions[session_id]['error'] = error
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        with _session_lock:
            return _active_sessions.get(session_id)
    
    @staticmethod
    def remove_session(session_id: str):
        """Remove session from active sessions."""
        with _session_lock:
            if session_id in _active_sessions:
                del _active_sessions[session_id]
                logger.info(f"Removed session: {session_id}")
    
    @staticmethod
    def is_video_processing(video_id: int) -> bool:
        """Check if a video is currently being processed."""
        with _session_lock:
            for session in _active_sessions.values():
                if session['video_id'] == video_id and session['status'] == 'processing':
                    return True
        return False


def extract_signals_for_timeframe(start_time: int, end_time: int, video_id: int) -> pd.DataFrame:
    """
    Extract signals from signals_data.csv within the given timeframe.
    Mirrors the logic from main.py lines 288-326.
    """
    signals_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "signals_data.csv")
    
    if not os.path.exists(signals_path):
        logger.error(f"❌ signals_data.csv not found at {signals_path}")
        return pd.DataFrame()
    
    try:
        signals = pd.read_csv(signals_path, header=None)
        PS = np.asanyarray(signals)
        
        new_data = []
        for j in range(len(PS)):
            timestamp_value = int(PS[j, 3])
            if start_time <= timestamp_value <= end_time:
                new_data.append(PS[j])
        
        if not new_data:
            return pd.DataFrame()
        
        new_df = pd.DataFrame(new_data)
        new_df.rename(columns={
            0: 'Time_series',
            1: 'GSR',
            2: 'HR',
            3: 'timestamp',
            4: 'time2'
        }, inplace=True)
        new_df["video_id"] = video_id
        
        return new_df
        
    except Exception as e:
        logger.error(f"Error extracting signals: {e}")
        return pd.DataFrame()


def extract_baseline_signals(baseline_start: int, baseline_end: int, video_id: int) -> pd.DataFrame:
    """
    Extract baseline signals (5 seconds before video start).
    Mirrors main.py lines 299-314.
    """
    signals_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "signals_data.csv")
    
    if not os.path.exists(signals_path):
        return pd.DataFrame()
    
    try:
        signals = pd.read_csv(signals_path, header=None)
        PS = np.asanyarray(signals)
        
        bs_data = []
        for j in range(1, len(PS)):
            timestamp_value = int(PS[j, 3])
            if baseline_start <= timestamp_value <= baseline_end:
                bs_data.append(PS[j])
        
        if not bs_data:
            return pd.DataFrame()
        
        bs_df = pd.DataFrame(bs_data)
        bs_df.rename(columns={
            0: 'Time_series',
            1: 'GSR',
            2: 'HR',
            3: 'timestamp',
            4: 'time2'
        }, inplace=True)
        bs_df["video_id"] = video_id
        
        return bs_df
        
    except Exception as e:
        logger.error(f"Error extracting baseline signals: {e}")
        return pd.DataFrame()


def compute_signal_diff(signal_df: pd.DataFrame, baseline_df: pd.DataFrame, 
                        video_id: int, start_time: int, predictions: List[int]) -> Optional[pd.DataFrame]:
    """
    Compute physiological differences between current window and baseline.
    Mirrors cal_physiological_diff.py get_signal_diff logic.
    Returns the feature row for this window.
    """
    if signal_df.empty or baseline_df.empty:
        return None
    
    try:
        # Calculate baseline means
        bs_data = baseline_df[['GSR', 'HR']].values
        GSR_meanblue = bs_data[:, 0].mean()
        HR_meanblue = bs_data[:, 1].mean()
        
        # Get video-specific valence/arousal
        valence, arousal = VIDEO_VALENCE_AROUSAL.get(video_id, (0, 0))
        
        # Filter signals for this video
        video_signals = signal_df[signal_df['video_id'] == video_id]
        if video_signals.empty:
            return None
        
        data = video_signals[['GSR', 'HR']].values
        window_size = 50
        
        if len(data) < window_size:
            # Not enough data for a window
            return None
        
        # Calculate differences for first window
        x = data[:window_size, :]
        xGSR_mean = x[:, 0].mean()
        xHR_mean = x[:, 1].mean()
        
        GSR_diff = abs(GSR_meanblue - xGSR_mean)
        HR_diff = abs(HR_meanblue - xHR_mean)
        
        # Previous window value
        prev_window = predictions[-1] if len(predictions) >= 1 else 2
        
        # Read the score file
        score_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  "score", f"{start_time}scores.csv")
        if not os.path.exists(score_path):
            logger.warning(f"Score file not found: {score_path}")
            return None
        
        scores = pd.read_csv(score_path)
        if scores.empty:
            return None
        
        score_value = scores['Score'].iloc[0]
        
        # Create feature row
        feature_row = pd.DataFrame([{
            'Start_time': start_time,
            'Score': score_value,
            'GSR_diff': GSR_diff,
            'HR_diff': HR_diff,
            'Previous_window': prev_window,
            'valence_acc_video': valence,
            'arousal_acc_video': arousal,
            'video_id': video_id
        }])
        
        return feature_row
        
    except Exception as e:
        logger.error(f"Error computing signal diff: {e}")
        return None


def append_feature_to_windowdata(feature_row: pd.DataFrame):
    """Append feature row to final/windowdata.csv"""
    final_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "final")
    os.makedirs(final_dir, exist_ok=True)
    
    windowdata_path = os.path.join(final_dir, "windowdata.csv")
    
    header_needed = not os.path.exists(windowdata_path) or os.path.getsize(windowdata_path) == 0
    
    with open(windowdata_path, 'a') as f:
        if header_needed:
            f.write("Start_time,Score,GSR_diff,HR_diff,Previous_window,valence_acc_video,arousal_acc_video,video_id\n")
        
        row = feature_row.iloc[0]
        f.write(f"{int(row['Start_time'])},{row['Score']},{row['GSR_diff']},{row['HR_diff']},"
                f"{int(row['Previous_window'])},{int(row['valence_acc_video'])},{int(row['arousal_acc_video'])},"
                f"{int(row['video_id'])}\n")


def get_model_input_from_windowdata(start_time: int) -> Optional[pd.DataFrame]:
    """
    Get the last 3 feature rows for LSTM input.
    Mirrors main.py lines 357-376.
    """
    windowdata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   "final", "windowdata.csv")
    
    if not os.path.exists(windowdata_path):
        return None
    
    try:
        final_feature = pd.read_csv(windowdata_path)
        
        if len(final_feature) < 3:
            return None
        
        # Find rows with this start_time
        index_values = final_feature.index[final_feature['Start_time'] == start_time].tolist()
        
        if not index_values:
            return None
        
        current_index = index_values[-1]  # Use latest match
        
        if current_index < 3:
            return None
        
        # Get previous 3 rows (not including current)
        previous_rows = final_feature.iloc[current_index - 3: current_index]
        
        # Select the 6 features the model expects
        testX = previous_rows[['Score', 'GSR_diff', 'HR_diff', 'Previous_window', 
                               'valence_acc_video', 'arousal_acc_video']]
        
        return testX
        
    except Exception as e:
        logger.error(f"Error getting model input: {e}")
        return None


def trigger_backend_pipeline(video_id: int, timestamp: int, user_id: str, session_id: str):
    """
    Trigger the full backend emotion analysis pipeline.
    
    This function ports the complete logic from main.py, including:
    1. Signal extraction from signals_data.csv
    2. Baseline extraction (5 seconds before video start)
    3. Change point score calculation
    4. Physiological difference calculation
    5. Feature generation
    6. LSTM model prediction
    
    Args:
        video_id: Video identifier (1-4)
        timestamp: Video start timestamp (milliseconds)
        user_id: User identifier
        session_id: Unique session identifier
    """
    try:
        logger.info(f"🎬 Starting backend pipeline for video {video_id} (session: {session_id})")
        VideoSessionManager.update_session_status(session_id, 'processing')
        
        # Import processing modules
        from cal_change_point import get_change_point_scores
        from model_prediction import get_model_prediction
        
        # Calculate timing
        duration_ms = VIDEO_DURATIONS.get(video_id, 150000)
        actual_end_time = timestamp + duration_ms
        baseline_start = timestamp - 5000  # 5 seconds before video start
        baseline_end = timestamp
        
        logger.info(f"📊 Video {video_id}: duration={duration_ms}ms, start={timestamp}, end={actual_end_time}")
        
        # Get or initialize user's cluster index
        global _user_cluster_indices
        nearest_centroid_index = _user_cluster_indices.get(user_id, 0)
        
        # For video 1, we need to do user profiling first
        if video_id == 1:
            logger.info("⏳ Video 1: Waiting full duration for user profiling...")
            time.sleep(duration_ms / 1000)
            
            # Extract signals for the full video
            signals_df = extract_signals_for_timeframe(timestamp, actual_end_time, video_id)
            
            if signals_df.empty:
                logger.warning(f"⚠️  No signals found for video {video_id}")
                VideoSessionManager.update_session_status(session_id, 'completed', 
                                                         'No signals found for user profiling')
                return
            
            logger.info(f"✅ Extracted {len(signals_df)} signals for user profiling")
            
            # Save signals for processing
            test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test")
            os.makedirs(test_dir, exist_ok=True)
            signals_df.to_csv(os.path.join(test_dir, f"online_{timestamp}.csv"), index=False)
            
            # Calculate change point scores
            logger.info("🔍 Calculating change point scores for profiling...")
            get_change_point_scores(signals_df, timestamp, window_size=50)
            
            # Load scores
            score_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      "score", f"{timestamp}scores.csv")
            if not os.path.exists(score_path):
                logger.error(f"❌ Score file not found: {score_path}")
                VideoSessionManager.update_session_status(session_id, 'error', 
                                                         'Failed to generate change scores')
                return
            
            score_df = pd.read_csv(score_path)
            
            if score_df.empty:
                logger.warning("⚠️  Empty score dataframe for profiling")
                VideoSessionManager.update_session_status(session_id, 'completed', 
                                                         'No scores generated for profiling')
                return
            
            # Do user profiling
            try:
                from profile_cluster_creation import do_cluster_newdata, do_new_user_label, nearest_cluster_allocation
                
                valence_arousal_vectors = do_cluster_newdata(score_df, "Score")
                new_vector = do_new_user_label(valence_arousal_vectors)
                nearest_centroid_index = nearest_cluster_allocation(new_vector)
                
                _user_cluster_indices[user_id] = nearest_centroid_index
                logger.info(f"👤 User {user_id} assigned to cluster {nearest_centroid_index}")
                
            except Exception as profile_error:
                logger.warning(f"⚠️  Profiling failed: {profile_error}, using default cluster 0")
                nearest_centroid_index = 0
                _user_cluster_indices[user_id] = 0
            
            VideoSessionManager.update_session_status(session_id, 'completed')
            logger.info(f"✅ Video 1 profiling completed for user {user_id}")
            return
        
        # For videos 2-4: Wait initial period then process in windows
        logger.info(f"⏳ Waiting 15 seconds for initial signal collection...")
        time.sleep(15)
        
        # Initialize prediction history
        predictions = [3, 2]  # Initial values from main.py
        prediction_count = 0
        
        # Process in 5-second windows
        for window_start in range(timestamp, actual_end_time, 5000):
            window_end = window_start + 15000  # 15 second window for signal collection
            
            # Wait until we have data for this window
            current_time_ms = int(time.time() * 1000)
            if window_end > current_time_ms:
                wait_time = (window_end - current_time_ms) / 1000
                logger.debug(f"⏳ Waiting {wait_time:.1f}s for window {window_start}")
                time.sleep(max(0, wait_time))
            
            # Clear active predictions near video end
            if window_start >= (actual_end_time - 20000):
                if DB_AVAILABLE:
                    try:
                        clear_active_predictions(video_id)
                        logger.info(f"🗑️  Cleared active predictions for video {video_id}")
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to clear predictions: {e}")
            
            # Extract signals for this window
            signals_df = extract_signals_for_timeframe(window_start, window_end, video_id)
            
            if signals_df.empty:
                logger.warning(f"⚠️  No signals for window {window_start}")
                continue
            
            # Extract baseline signals
            baseline_df = extract_baseline_signals(baseline_start, baseline_end, video_id)
            
            if baseline_df.empty:
                logger.warning(f"⚠️  No baseline signals for window {window_start}")
                continue
            
            # Save signals
            test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test")
            os.makedirs(test_dir, exist_ok=True)
            signals_df.to_csv(os.path.join(test_dir, f"online_{window_start}.csv"), index=False)
            baseline_df.to_csv(os.path.join(test_dir, "bs_data.csv"), index=False)
            
            # Calculate change point scores
            logger.debug(f"🔍 Calculating change scores for window {window_start}")
            get_change_point_scores(signals_df, window_start, window_size=50)
            
            # Check if score file was created
            score_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      "score", f"{window_start}scores.csv")
            if not os.path.exists(score_path):
                logger.warning(f"⚠️  Score file not created for window {window_start}")
                continue
            
            score_df = pd.read_csv(score_path)
            if score_df.empty:
                logger.warning(f"⚠️  Empty scores for window {window_start}")
                continue
            
            # Compute physiological differences and create feature row
            feature_row = compute_signal_diff(signals_df, baseline_df, video_id, 
                                              window_start, predictions)
            
            if feature_row is None:
                logger.warning(f"⚠️  Could not compute features for window {window_start}")
                continue
            
            # Append to windowdata.csv
            append_feature_to_windowdata(feature_row)
            
            # Get model input (needs 3 previous rows)
            testX = get_model_input_from_windowdata(window_start)
            
            if testX is None or len(testX) < 3:
                logger.debug(f"⏳ Not enough history for prediction at {window_start}")
                continue
            
            # Make prediction
            try:
                y_pred_class = get_model_prediction(testX, nearest_centroid_index, 
                                                    window_start, video_id, 
                                                    user_id, session_id)
                predictions.append(y_pred_class.item())
                prediction_count += 1
                logger.info(f"✅ Prediction {prediction_count} generated for window {window_start}")
                
            except Exception as pred_error:
                logger.error(f"❌ Prediction error at {window_start}: {pred_error}")
                continue
        
        logger.info(f"🎉 Completed processing: {prediction_count} predictions generated for video {video_id}")
        VideoSessionManager.update_session_status(session_id, 'completed')
        
    except Exception as e:
        logger.error(f"❌ Pipeline error for session {session_id}: {e}", exc_info=True)
        VideoSessionManager.update_session_status(session_id, 'error', str(e))
    
    finally:
        # Cleanup: Remove session after some time
        time.sleep(300)  # Keep session info for 5 minutes
        VideoSessionManager.remove_session(session_id)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@video_session_bp.route('/api/video/start', methods=['POST'])
def start_video_processing():
    """
    API endpoint: Start video processing
    
    Called by frontend when user starts playing a video.
    Triggers the emotion analysis pipeline in a background thread.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        video_id = data.get('video_id')
        timestamp = data.get('timestamp', int(time.time() * 1000))
        user_id = data.get('user_id', 'anonymous')
        session_id = data.get('session_id', f"{user_id}_{video_id}_{timestamp}")
        
        if not video_id:
            return jsonify({'error': 'video_id is required'}), 400
        
        if video_id not in VIDEO_DURATIONS:
            return jsonify({
                'error': f'Invalid video_id. Must be one of: {list(VIDEO_DURATIONS.keys())}'
            }), 400
        
        if VideoSessionManager.is_video_processing(video_id):
            return jsonify({
                'error': f'Video {video_id} is already being processed',
                'status': 'already_processing'
            }), 409
        
        VideoSessionManager.create_session(video_id, timestamp, user_id, session_id)
        
        if DB_AVAILABLE:
            try:
                insert_video_start(timestamp, video_id, user_id, session_id)
                logger.info(f"📊 Recorded video start: video={video_id}, user={user_id}")
            except Exception as db_error:
                logger.error(f"⚠️  Database insert failed: {db_error}")
        
        processing_thread = threading.Thread(
            target=trigger_backend_pipeline,
            args=(video_id, timestamp, user_id, session_id),
            daemon=True,
            name=f"VideoProcessor-{session_id}"
        )
        processing_thread.start()
        
        logger.info(f"✅ Started processing thread for session {session_id}")
        
        return jsonify({
            'status': 'success',
            'video_id': video_id,
            'timestamp': timestamp,
            'session_id': session_id,
            'estimated_duration_ms': VIDEO_DURATIONS[video_id],
            'message': 'Backend emotion analysis pipeline started'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in start_video_processing: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@video_session_bp.route('/api/video/stop', methods=['POST'])
def stop_video_processing():
    """API endpoint: Stop video processing (optional)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        session_id = data.get('session_id')
        video_id = data.get('video_id')
        
        if session_id:
            session = VideoSessionManager.get_session(session_id)
            if session:
                VideoSessionManager.update_session_status(session_id, 'stopped')
                logger.info(f"🛑 Session {session_id} marked as stopped")
        
        return jsonify({
            'status': 'success',
            'message': 'Stop signal received'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in stop_video_processing: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@video_session_bp.route('/api/video/session/<session_id>', methods=['GET'])
def get_session_status(session_id: str):
    """API endpoint: Get session status"""
    session = VideoSessionManager.get_session(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        'video_id': session['video_id'],
        'user_id': session['user_id'],
        'status': session['status'],
        'error': session.get('error'),
        'started_at': session['start_time'].isoformat()
    }), 200


@video_session_bp.route('/api/video/sessions/active', methods=['GET'])
def get_active_sessions():
    """API endpoint: Get all active sessions"""
    with _session_lock:
        sessions = []
        for session_id, session in _active_sessions.items():
            sessions.append({
                'session_id': session_id,
                'video_id': session['video_id'],
                'user_id': session['user_id'],
                'status': session['status'],
                'error': session.get('error'),
                'started_at': session['start_time'].isoformat()
            })
    
    return jsonify({
        'active_sessions': sessions,
        'total': len(sessions)
    }), 200


@video_session_bp.route('/api/video/health', methods=['GET'])
def health_check():
    """API endpoint: Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'video_session_manager',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(_active_sessions)
    }), 200
