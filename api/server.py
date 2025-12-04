"""
Emotion Analysis API Server
Provides REST endpoints for emotion tracking, predictions, and physiological data.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import sys
import os
import logging

# Add parent directory to path to import db_models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_models import (
    get_active_predictions,
    get_all_predictions,
    get_signals_by_timestamp_range,
    get_all_signals,
    get_change_scores,
    get_all_features,
    get_features_by_video,
    get_video_starts_by_id,
    get_latest_video_start,
    get_database_stats,
    get_collection
)

# Import video session manager blueprint
from api.video_session_manager import video_session_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Register video session blueprint
app.register_blueprint(video_session_bp)
logger.info("✅ Video session manager registered")

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'Emotion Analysis API',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'stats': '/api/stats',
            'predictions': '/api/predictions',
            'emotions': '/api/emotions',
            'signals': '/api/signals',
            'videos': '/api/videos',
            'video_session': '/api/video'
        },
        'new_features': {
            'video_start': 'POST /api/video/start',
            'video_stop': 'POST /api/video/stop',
            'video_predictions': 'GET /api/predictions/video/<video_id>',
            'session_status': 'GET /api/video/session/<session_id>'
        }
    })

@app.route('/api/health')
def health():
    """Check API and database health"""
    try:
        stats = get_database_stats()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat(),
            'collections': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stats')
def stats():
    """Get database statistics"""
    try:
        stats = get_database_stats()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# PREDICTION ENDPOINTS (Opportune Moments)
# ============================================================================

@app.route('/api/predictions/active')
def get_active_preds():
    """
    Get active predictions for current video
    Used for real-time display on frontend
    
    Query params:
    - video_id (optional): Filter by video ID
    - user_id (optional): Filter by user (for multi-user support)
    - session_id (optional): Filter by session
    """
    try:
        video_id = request.args.get('video_id', type=int)
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        
        # Pass all filters to get_active_predictions
        predictions = get_active_predictions(video_id, user_id, session_id)
        
        # Convert ObjectId to string for JSON serialization
        result = []
        for pred in predictions:
            result.append({
                'id': str(pred['_id']),
                'starttime': pred['starttime'],
                'video_no': pred['video_no'],
                'probe': pred['probe'],  # HH, HL, LH, LL
                'user_id': pred.get('user_id'),  # Include if present
                'session_id': pred.get('session_id'),  # Include if present
                'created_at': pred['created_at'].isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions/all')
def get_all_preds():
    """
    Get all historical predictions
    
    Query params:
    - limit (optional): Number of records to return (default: 100)
    - offset (optional): Offset for pagination (default: 0)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        collection = get_collection('predictions')
        predictions = list(collection.find().sort('created_at', -1).skip(offset).limit(limit))
        
        result = []
        for pred in predictions:
            result.append({
                'id': str(pred['_id']),
                'starttime': pred['starttime'],
                'video_no': pred['video_no'],
                'probe': pred['probe'],
                'cluster_id': pred.get('cluster_id', 0),
                'created_at': pred['created_at'].isoformat()
            })
        
        total_count = collection.count_documents({})
        
        return jsonify({
            'success': True,
            'count': len(result),
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predictions/video/<int:video_id>')
def get_predictions_by_video(video_id):
    """
    Get all predictions for a specific video with frontend-ready formatting
    
    Returns segments with emotions and colors for timeline display.
    This endpoint is optimized for frontend consumption.
    
    URL Parameters:
    - video_id: Video identifier (1-4)
    
    Query Parameters:
    - user_id (optional): Filter by user
    - session_id (optional): Filter by session
    
    Response Format:
    {
        "success": true,
        "video_id": 2,
        "segments": [
            {
                "segment_index": 0,
                "timestamp": 1742305079661,
                "probe": "HL",
                "emotion": "Neutral",
                "color": "#7fc087"
            }
        ],
        "total": 30,
        "duration_ms": 151000
    }
    """
    try:
        # Get optional filters
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        
        # Query predictions for this video
        collection = get_collection('predictions')
        query = {'video_no': video_id}
        
        # Add filters if provided (for multi-user support)
        # Skip filtering if user_id is 'anonymous' (default/no login)
        if user_id and user_id != 'anonymous':
            query['user_id'] = user_id
        if session_id:
            query['session_id'] = session_id
        
        predictions = list(collection.find(query).sort('starttime', 1))
        
        # Emotion mapping (Valence-Arousal to emotion labels)
        emotion_map = {
            'HH': 'Happy',      # High valence, high arousal → Happy/Excited
            'HL': 'Neutral',    # High valence, low arousal → Calm/Peaceful
            'LH': 'Angry',      # Low valence, high arousal → Anxious/Angry
            'LL': 'Sad'         # Low valence, low arousal → Sad/Bored
        }
        
        # Color mapping (same as old frontend for consistency)
        color_map = {
            'HH': '#eecdac',  # Beige - Highly opportune
            'HL': '#7fc087',  # Green - Moderately opportune
            'LH': '#f4978e',  # Pink - Building opportune
            'LL': '#879af0'   # Blue - Not opportune
        }
        
        # Video duration mapping (milliseconds)
        video_durations = {
            1: 180000,  # 180 seconds
            2: 151000,  # 151 seconds
            3: 160000,  # 160 seconds
            4: 117000   # 117 seconds
        }
        
        # Transform predictions to segments
        segments = []
        for idx, pred in enumerate(predictions):
            probe = pred.get('probe', '')
            timestamp = pred.get('starttime', 0)
            
            segments.append({
                'segment_index': idx,
                'timestamp': timestamp,
                'probe': probe,
                'emotion': emotion_map.get(probe, 'Neutral'),
                'color': color_map.get(probe, '#999999'),
                'cluster_id': pred.get('cluster_id', 0)
            })
        
        logger.info(f"📊 Retrieved {len(segments)} predictions for video {video_id}")
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'segments': segments,
            'total': len(segments),
            'duration_ms': video_durations.get(video_id, 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching predictions for video {video_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'video_id': video_id
        }), 500

@app.route('/api/predictions/timeline')
def get_predictions_timeline():
    """
    Get predictions formatted for timeline display
    Returns predictions with 5-second segments
    
    Query params:
    - video_id (required): Video ID
    """
    try:
        video_id = request.args.get('video_id', type=int)
        if video_id is None:
            return jsonify({
                'success': False,
                'error': 'video_id parameter is required'
            }), 400
        
        collection = get_collection('active_predictions')
        predictions = list(collection.find({'video_no': video_id}).sort('starttime', 1))
        
        # Format for timeline with emotion labels
        emotion_map = {
            'HH': 'High Opportuneness (Positive)',
            'HL': 'Moderate Opportuneness (Transitioning)',
            'LH': 'Moderate Opportuneness (Building)',
            'LL': 'Low Opportuneness (Not Opportune)'
        }
        
        color_map = {
            'HH': '#eecdac',  # Beige
            'HL': '#7fc087',  # Green
            'LH': '#f4978e',  # Red/Pink
            'LL': '#879af0'   # Blue
        }
        
        result = []
        for pred in predictions:
            result.append({
                'starttime': pred['starttime'],
                'video_no': pred['video_no'],
                'probe': pred['probe'],
                'emotion_label': emotion_map.get(pred['probe'], 'Unknown'),
                'color': color_map.get(pred['probe'], '#999999'),
                'segment_duration': 5000,  # 5 seconds in milliseconds
                'created_at': pred['created_at'].isoformat()
            })
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'count': len(result),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# EMOTION / FEATURES ENDPOINTS
# ============================================================================

@app.route('/api/emotions/current')
def get_current_emotions():
    """
    Get current emotional state based on latest features
    Returns valence, arousal, and physiological differences
    """
    try:
        collection = get_collection('features')
        latest_feature = collection.find_one(sort=[('created_at', -1)])
        
        if not latest_feature:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No emotion data available yet'
            })
        
        # Map valence/arousal to emotion quadrants
        valence = latest_feature['valence_acc_video']
        arousal = latest_feature['arousal_acc_video']
        
        emotion_quadrant = {
            (1, 1): 'High Valence, High Arousal (Happy/Excited)',
            (1, 0): 'High Valence, Low Arousal (Calm/Peaceful)',
            (0, 1): 'Low Valence, High Arousal (Anxious/Stressed)',
            (0, 0): 'Low Valence, Low Arousal (Sad/Bored)'
        }
        
        result = {
            'start_time': latest_feature['start_time'],
            'video_id': latest_feature['video_id'],
            'valence': valence,
            'arousal': arousal,
            'emotion_quadrant': emotion_quadrant.get((valence, arousal), 'Unknown'),
            'change_score': latest_feature['score'],
            'gsr_diff': latest_feature['gsr_diff'],
            'hr_diff': latest_feature['hr_diff'],
            'previous_window': latest_feature['previous_window'],
            'created_at': latest_feature['created_at'].isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/emotions/history')
def get_emotions_history():
    """
    Get emotion history with time range filter
    
    Query params:
    - start_time (optional): Start timestamp
    - end_time (optional): End timestamp
    - video_id (optional): Filter by video
    - limit (optional): Number of records (default: 100)
    """
    try:
        start_time = request.args.get('start_time', type=int)
        end_time = request.args.get('end_time', type=int)
        video_id = request.args.get('video_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        query = {}
        if start_time and end_time:
            query['start_time'] = {'$gte': start_time, '$lte': end_time}
        if video_id is not None:
            query['video_id'] = video_id
        
        collection = get_collection('features')
        features = list(collection.find(query).sort('start_time', 1).limit(limit))
        
        result = []
        for feature in features:
            result.append({
                'id': str(feature['_id']),
                'start_time': feature['start_time'],
                'video_id': feature['video_id'],
                'valence': feature['valence_acc_video'],
                'arousal': feature['arousal_acc_video'],
                'change_score': feature['score'],
                'gsr_diff': feature['gsr_diff'],
                'hr_diff': feature['hr_diff'],
                'created_at': feature['created_at'].isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/emotions/video/<int:video_id>')
def get_emotions_by_video(video_id):
    """
    Get all emotions for a specific video
    Shows emotional journey throughout the video
    """
    try:
        collection = get_collection('features')
        features = list(collection.find({'video_id': video_id}).sort('start_time', 1))
        
        result = []
        for feature in features:
            result.append({
                'start_time': feature['start_time'],
                'valence': feature['valence_acc_video'],
                'arousal': feature['arousal_acc_video'],
                'change_score': feature['score'],
                'gsr_diff': feature['gsr_diff'],
                'hr_diff': feature['hr_diff'],
                'segment_number': len(result) + 1
            })
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'count': len(result),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# PHYSIOLOGICAL SIGNALS ENDPOINTS
# ============================================================================

@app.route('/api/signals/latest')
def get_latest_signals():
    """
    Get latest physiological signals
    
    Query params:
    - count (optional): Number of latest readings (default: 50)
    """
    try:
        count = request.args.get('count', 50, type=int)
        
        collection = get_collection('signals')
        signals = list(collection.find().sort('timestamp', -1).limit(count))
        
        result = []
        for signal in signals:
            result.append({
                'time_series': signal['time_series'],
                'gsr': signal['gsr'],
                'hr': signal['hr'],
                'timestamp': signal['timestamp'],
                'datetime': signal.get('datetime', ''),
                'created_at': signal['created_at'].isoformat()
            })
        
        # Reverse to get chronological order
        result.reverse()
        
        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/signals/range')
def get_signals_range():
    """
    Get signals within a time range
    
    Query params:
    - start_time (required): Start timestamp in milliseconds
    - end_time (required): End timestamp in milliseconds
    """
    try:
        start_time = request.args.get('start_time', type=int)
        end_time = request.args.get('end_time', type=int)
        
        if start_time is None or end_time is None:
            return jsonify({
                'success': False,
                'error': 'start_time and end_time parameters are required'
            }), 400
        
        df = get_signals_by_timestamp_range(start_time, end_time)
        
        if df.empty:
            return jsonify({
                'success': True,
                'count': 0,
                'data': [],
                'message': 'No signals found in this time range'
            })
        
        # Convert DataFrame to list of dicts
        result = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'count': len(result),
            'start_time': start_time,
            'end_time': end_time,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/signals/stats')
def get_signals_stats():
    """
    Get statistical summary of recent signals
    """
    try:
        # Get last 100 signals
        collection = get_collection('signals')
        signals = list(collection.find().sort('timestamp', -1).limit(100))
        
        if not signals:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No signals available'
            })
        
        gsr_values = [s['gsr'] for s in signals]
        hr_values = [s['hr'] for s in signals]
        
        import numpy as np
        
        stats = {
            'gsr': {
                'mean': float(np.mean(gsr_values)),
                'std': float(np.std(gsr_values)),
                'min': int(np.min(gsr_values)),
                'max': int(np.max(gsr_values))
            },
            'hr': {
                'mean': float(np.mean(hr_values)),
                'std': float(np.std(hr_values)),
                'min': int(np.min(hr_values)),
                'max': int(np.max(hr_values))
            },
            'sample_count': len(signals),
            'time_range': {
                'start': signals[-1]['timestamp'],
                'end': signals[0]['timestamp']
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# VIDEO TRACKING ENDPOINTS
# ============================================================================

@app.route('/api/videos/current')
def get_current_video():
    """Get currently playing video information"""
    try:
        latest = get_latest_video_start()
        
        if not latest:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No video currently playing'
            })
        
        result = {
            'video_id': latest['video_id'],
            'start_timestamp': latest['timestamp'],
            'started_at': latest['created_at'].isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/videos/history')
def get_videos_history():
    """Get all video playback history"""
    try:
        collection = get_collection('video_starts')
        videos = list(collection.find().sort('created_at', -1))
        
        result = []
        for video in videos:
            result.append({
                'id': str(video['_id']),
                'video_id': video['video_id'],
                'timestamp': video['timestamp'],
                'started_at': video['created_at'].isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# USER SESSION / TRACKING ENDPOINTS
# ============================================================================

@app.route('/api/session/summary')
def get_session_summary():
    """
    Get complete session summary
    Includes all videos watched, emotions experienced, predictions made
    """
    try:
        stats = get_database_stats()
        
        # Get video count
        video_collection = get_collection('video_starts')
        videos = list(video_collection.find().sort('created_at', 1))
        
        # Get emotion distribution
        feature_collection = get_collection('features')
        features = list(feature_collection.find())
        
        emotion_dist = {
            'high_valence_high_arousal': 0,
            'high_valence_low_arousal': 0,
            'low_valence_high_arousal': 0,
            'low_valence_low_arousal': 0
        }
        
        for feature in features:
            v = feature['valence_acc_video']
            a = feature['arousal_acc_video']
            if v == 1 and a == 1:
                emotion_dist['high_valence_high_arousal'] += 1
            elif v == 1 and a == 0:
                emotion_dist['high_valence_low_arousal'] += 1
            elif v == 0 and a == 1:
                emotion_dist['low_valence_high_arousal'] += 1
            else:
                emotion_dist['low_valence_low_arousal'] += 1
        
        # Get prediction distribution
        pred_collection = get_collection('predictions')
        predictions = list(pred_collection.find())
        
        prediction_dist = {'HH': 0, 'HL': 0, 'LH': 0, 'LL': 0}
        for pred in predictions:
            probe = pred.get('probe', '')
            if probe in prediction_dist:
                prediction_dist[probe] += 1
        
        summary = {
            'session_stats': stats,
            'videos_watched': len(videos),
            'video_list': [v['video_id'] for v in videos],
            'total_predictions': stats.get('predictions', 0),
            'emotion_distribution': emotion_dist,
            'prediction_distribution': prediction_dist,
            'session_duration': {
                'start': videos[0]['created_at'].isoformat() if videos else None,
                'latest': videos[-1]['created_at'].isoformat() if videos else None
            }
        }
        
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/session/emotion-timeline')
def get_emotion_timeline():
    """
    Get complete emotion timeline for visualization
    Shows how user emotions changed over time across all videos
    """
    try:
        collection = get_collection('features')
        features = list(collection.find().sort('start_time', 1))
        
        timeline = []
        for i, feature in enumerate(features):
            v = feature['valence_acc_video']
            a = feature['arousal_acc_video']
            
            emotion_label = {
                (1, 1): 'Happy/Excited',
                (1, 0): 'Calm/Peaceful',
                (0, 1): 'Anxious/Stressed',
                (0, 0): 'Sad/Bored'
            }.get((v, a), 'Unknown')
            
            timeline.append({
                'segment': i + 1,
                'start_time': feature['start_time'],
                'video_id': feature['video_id'],
                'emotion': emotion_label,
                'valence': v,
                'arousal': a,
                'gsr_diff': feature['gsr_diff'],
                'hr_diff': feature['hr_diff'],
                'change_score': feature['score']
            })
        
        return jsonify({
            'success': True,
            'count': len(timeline),
            'data': timeline,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 SURJA Emotion Tracking API Server")
    print("="*70)
    print("\n📍 Server running on: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000/")
    print("\n🔗 Available Endpoints:")
    print("   • Health Check: http://localhost:5000/api/health")
    print("   • Active Predictions: http://localhost:5000/api/predictions/active")
    print("   • Current Emotions: http://localhost:5000/api/emotions/current")
    print("   • Latest Signals: http://localhost:5000/api/signals/latest")
    print("   • Session Summary: http://localhost:5000/api/session/summary")
    print("\n⌨️  Press Ctrl+C to stop the server\n")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

