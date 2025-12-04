"""
MongoDB Data Models and Helper Functions for SURJA System
Provides CRUD operations for all collections
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from db_config import get_collection, logger


# ============================================================================
# SIGNALS COLLECTION (replaces signals_data.csv)
# ============================================================================

def insert_signal(data: Dict[str, Any]) -> bool:
    """
    Insert a single physiological signal reading
    
    Args:
        data: Dict with keys: time_series, gsr, hr, timestamp, datetime
              Optional keys: user_id, video_id, session_id (for multi-user support)
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('signals')
        document = {
            'time_series': int(data.get('time_series', 0)),
            'gsr': int(data.get('gsr', 0)),
            'hr': int(data.get('hr', 0)),
            'timestamp': int(data.get('timestamp', 0)),
            'datetime': data.get('datetime'),
            'created_at': datetime.now()
        }
        
        # Add optional fields if provided (backward compatible)
        if 'user_id' in data and data['user_id'] is not None:
            document['user_id'] = str(data['user_id'])
        if 'video_id' in data and data['video_id'] is not None:
            document['video_id'] = int(data['video_id'])
        if 'session_id' in data and data['session_id'] is not None:
            document['session_id'] = str(data['session_id'])
        
        collection.insert_one(document)
        return True
    except Exception as e:
        logger.error(f"Error inserting signal: {e}")
        return False


def insert_signals_bulk(data_list: List[Dict[str, Any]]) -> bool:
    """
    Insert multiple signal readings in bulk (more efficient)
    
    Args:
        data_list: List of signal dictionaries
                   Optional keys in each dict: user_id, video_id, session_id (for multi-user support)
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('signals')
        documents = []
        for data in data_list:
            doc = {
                'time_series': int(data.get('time_series', 0)),
                'gsr': int(data.get('gsr', 0)),
                'hr': int(data.get('hr', 0)),
                'timestamp': int(data.get('timestamp', 0)),
                'datetime': data.get('datetime'),
                'created_at': datetime.now()
            }
            
            # Add optional fields if provided (backward compatible)
            if 'user_id' in data and data['user_id'] is not None:
                doc['user_id'] = str(data['user_id'])
            if 'video_id' in data and data['video_id'] is not None:
                doc['video_id'] = int(data['video_id'])
            if 'session_id' in data and data['session_id'] is not None:
                doc['session_id'] = str(data['session_id'])
            
            documents.append(doc)
        
        collection.insert_many(documents)
        return True
    except Exception as e:
        logger.error(f"Error inserting signals bulk: {e}")
        return False


def get_signals_by_timestamp_range(start_timestamp: int, end_timestamp: int) -> pd.DataFrame:
    """
    Get signals within a timestamp range
    
    Args:
        start_timestamp: Start time in milliseconds
        end_timestamp: End time in milliseconds
    
    Returns:
        DataFrame with signal data
    """
    try:
        collection = get_collection('signals')
        query = {
            'timestamp': {
                '$gte': start_timestamp,
                '$lte': end_timestamp
            }
        }
        cursor = collection.find(query).sort('timestamp', 1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            # Rename columns to match current CSV format
            df = df.rename(columns={
                'time_series': 'Time_series',
                'gsr': 'GSR',
                'hr': 'HR',
                'datetime': 'time2'
            })
            return df[['Time_series', 'GSR', 'HR', 'timestamp', 'time2']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return pd.DataFrame()


def get_all_signals() -> pd.DataFrame:
    """
    Get all signals (use with caution - can be large)
    
    Returns:
        DataFrame with all signal data
    """
    try:
        collection = get_collection('signals')
        cursor = collection.find().sort('timestamp', 1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'time_series': 'Time_series',
                'gsr': 'GSR',
                'hr': 'HR',
                'datetime': 'time2'
            })
            return df[['Time_series', 'GSR', 'HR', 'timestamp', 'time2']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting all signals: {e}")
        return pd.DataFrame()


# ============================================================================
# VIDEO STARTS COLLECTION (replaces downloaded/start_times_X.csv)
# ============================================================================

def insert_video_start(timestamp: int, video_id: int, user_id: str = None, session_id: str = None) -> bool:
    """
    Insert video start event
    
    Args:
        timestamp: Start time in milliseconds
        video_id: Video identifier
        user_id: User identifier (optional, for multi-user support)
        session_id: Session identifier (optional, for tracking)
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('video_starts')
        document = {
            'timestamp': int(timestamp),
            'video_id': int(video_id),
            'created_at': datetime.now()
        }
        
        # Add user_id if provided (backward compatible)
        if user_id is not None:
            document['user_id'] = str(user_id)
        
        # Add session_id if provided (backward compatible)
        if session_id is not None:
            document['session_id'] = str(session_id)
        
        collection.insert_one(document)
        log_msg = f"✅ Video start recorded: video_id={video_id}, timestamp={timestamp}"
        if user_id:
            log_msg += f", user_id={user_id}"
        if session_id:
            log_msg += f", session_id={session_id}"
        logger.info(log_msg)
        return True
    except Exception as e:
        logger.error(f"Error inserting video start: {e}")
        return False


def get_latest_video_start() -> Optional[Dict[str, Any]]:
    """
    Get the most recent video start event
    
    Returns:
        Dict with timestamp and video_id, or None
    """
    try:
        collection = get_collection('video_starts')
        result = collection.find_one(sort=[('created_at', -1)])
        return result
    except Exception as e:
        logger.error(f"Error getting latest video start: {e}")
        return None


def get_video_starts_by_id(video_id: int) -> List[Dict[str, Any]]:
    """
    Get all start events for a specific video
    
    Args:
        video_id: Video identifier
    
    Returns:
        List of video start documents
    """
    try:
        collection = get_collection('video_starts')
        cursor = collection.find({'video_id': video_id}).sort('created_at', -1)
        return list(cursor)
    except Exception as e:
        logger.error(f"Error getting video starts: {e}")
        return []


# ============================================================================
# WINDOWED DATA COLLECTION (replaces test/online_X.csv and test/bs_data.csv)
# ============================================================================

def insert_windowed_data(data: pd.DataFrame, start_time: int, window_type: str = 'online') -> bool:
    """
    Insert windowed physiological data
    
    Args:
        data: DataFrame with windowed data
        start_time: Window start time
        window_type: 'online' or 'baseline'
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('windowed_data')
        documents = []
        
        for _, row in data.iterrows():
            documents.append({
                'start_time': int(start_time),
                'time_series': int(row.get('Time_series', 0)),
                'gsr': float(row.get('GSR', 0)),
                'hr': float(row.get('HR', 0)),
                'timestamp': int(row.get('timestamp', 0)),
                'time2': str(row.get('time2', '')),
                'video_id': int(row.get('video_id', 0)),
                'window_type': window_type,
                'created_at': datetime.now()
            })
        
        if documents:
            collection.insert_many(documents)
            return True
        return False
    except Exception as e:
        logger.error(f"Error inserting windowed data: {e}")
        return False


def get_windowed_data(start_time: int, window_type: str = 'online') -> pd.DataFrame:
    """
    Get windowed data for a specific time window
    
    Args:
        start_time: Window start time
        window_type: 'online' or 'baseline'
    
    Returns:
        DataFrame with windowed data
    """
    try:
        collection = get_collection('windowed_data')
        query = {
            'start_time': start_time,
            'window_type': window_type
        }
        cursor = collection.find(query).sort('timestamp', 1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'time_series': 'Time_series',
                'gsr': 'GSR',
                'hr': 'HR',
                'time2': 'time2'
            })
            return df[['Time_series', 'GSR', 'HR', 'timestamp', 'time2', 'video_id']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting windowed data: {e}")
        return pd.DataFrame()


# ============================================================================
# CHANGE SCORES COLLECTION (replaces score/Xscores.csv)
# ============================================================================

def insert_change_score(start_time: int, start: int, border: int, end: int, score: float) -> bool:
    """
    Insert change point detection score
    
    Args:
        start_time: Window start time identifier
        start: Window start timestamp
        border: Window border timestamp
        end: Window end timestamp
        score: Change point score
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('change_scores')
        document = {
            'start_time': int(start_time),
            'start': int(start),
            'border': int(border),
            'end': int(end),
            'score': float(score),
            'created_at': datetime.now()
        }
        collection.insert_one(document)
        return True
    except Exception as e:
        logger.error(f"Error inserting change score: {e}")
        return False


def get_change_scores(start_time: int) -> pd.DataFrame:
    """
    Get change point scores for a specific start time
    
    Args:
        start_time: Window start time identifier
    
    Returns:
        DataFrame with change scores
    """
    try:
        collection = get_collection('change_scores')
        query = {'start_time': start_time}
        cursor = collection.find(query).sort('start', 1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            # Match CSV format
            df = df.rename(columns={
                'start': 'Start',
                'border': 'Border',
                'end': 'End',
                'score': 'Score'
            })
            return df[['Start', 'Border', 'End', 'Score']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting change scores: {e}")
        return pd.DataFrame()


# ============================================================================
# FEATURES COLLECTION (replaces final/windowdata.csv)
# ============================================================================

def insert_feature(data: Dict[str, Any]) -> bool:
    """
    Insert extracted features for ML model
    
    Args:
        data: Dict with feature values
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('features')
        document = {
            'start_time': int(data.get('start_time', 0)),
            'score': float(data.get('score', 0)),
            'gsr_diff': float(data.get('gsr_diff', 0)),
            'hr_diff': float(data.get('hr_diff', 0)),
            'previous_window': int(data.get('previous_window', 0)),
            'valence_acc_video': int(data.get('valence_acc_video', 0)),
            'arousal_acc_video': int(data.get('arousal_acc_video', 0)),
            'video_id': int(data.get('video_id', 0)),
            'created_at': datetime.now()
        }
        collection.insert_one(document)
        return True
    except Exception as e:
        logger.error(f"Error inserting feature: {e}")
        return False


def get_all_features() -> pd.DataFrame:
    """
    Get all extracted features (for model training/prediction)
    
    Returns:
        DataFrame with all features
    """
    try:
        collection = get_collection('features')
        cursor = collection.find().sort('start_time', 1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'start_time': 'Start_time',
                'score': 'Score',
                'gsr_diff': 'GSR_diff',
                'hr_diff': 'HR_diff',
                'previous_window': 'Previous_window',
                'valence_acc_video': 'valence_acc_video',
                'arousal_acc_video': 'arousal_acc_video',
                'video_id': 'video_id'
            })
            return df[['Start_time', 'Score', 'GSR_diff', 'HR_diff', 'Previous_window', 
                      'valence_acc_video', 'arousal_acc_video', 'video_id']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        return pd.DataFrame()


def get_features_by_video(video_id: int) -> pd.DataFrame:
    """
    Get features for a specific video
    
    Args:
        video_id: Video identifier
    
    Returns:
        DataFrame with features
    """
    try:
        collection = get_collection('features')
        query = {'video_id': video_id}
        cursor = collection.find(query).sort('start_time', 1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'start_time': 'Start_time',
                'score': 'Score',
                'gsr_diff': 'GSR_diff',
                'hr_diff': 'HR_diff',
                'previous_window': 'Previous_window'
            })
            return df[['Start_time', 'Score', 'GSR_diff', 'HR_diff', 'Previous_window', 
                      'valence_acc_video', 'arousal_acc_video', 'video_id']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting features by video: {e}")
        return pd.DataFrame()


# ============================================================================
# PREDICTIONS COLLECTION (replaces Predictions/predict.csv)
# ============================================================================

def insert_prediction(starttime: int, video_no: int, probe: str, cluster_id: int = 0, 
                     user_id: str = None, session_id: str = None) -> bool:
    """
    Insert prediction (permanent log)
    
    Args:
        starttime: Prediction timestamp
        video_no: Video number
        probe: Prediction label (HH, HL, LH, LL)
        cluster_id: User cluster ID
        user_id: User identifier (optional, for multi-user support)
        session_id: Session identifier (optional, for tracking)
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('predictions')
        document = {
            'starttime': int(starttime),
            'video_no': int(video_no),
            'probe': str(probe),
            'cluster_id': int(cluster_id),
            'created_at': datetime.now()
        }
        
        # Add user_id if provided (backward compatible)
        if user_id is not None:
            document['user_id'] = str(user_id)
        
        # Add session_id if provided (backward compatible)
        if session_id is not None:
            document['session_id'] = str(session_id)
        
        collection.insert_one(document)
        return True
    except Exception as e:
        logger.error(f"Error inserting prediction: {e}")
        return False


def get_all_predictions() -> pd.DataFrame:
    """
    Get all predictions
    
    Returns:
        DataFrame with all predictions
    """
    try:
        collection = get_collection('predictions')
        cursor = collection.find().sort('created_at', -1)
        data = list(cursor)
        
        if data:
            df = pd.DataFrame(data)
            return df[['starttime', 'video_no', 'probe', 'cluster_id', 'created_at']]
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        return pd.DataFrame()


# ============================================================================
# ACTIVE PREDICTIONS COLLECTION (replaces annotation_interface/public/pred.csv)
# ============================================================================

def insert_active_prediction(starttime: int, video_no: int, probe: str, 
                            user_id: str = None, session_id: str = None) -> bool:
    """
    Insert active prediction (for frontend display)
    
    Args:
        starttime: Prediction timestamp
        video_no: Video number
        probe: Prediction label (HH, HL, LH, LL)
        user_id: User identifier (optional, for multi-user support)
        session_id: Session identifier (optional, for tracking)
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('active_predictions')
        document = {
            'starttime': int(starttime),
            'video_no': int(video_no),
            'probe': str(probe),
            'created_at': datetime.now()
        }
        
        # Add user_id if provided (backward compatible)
        if user_id is not None:
            document['user_id'] = str(user_id)
        
        # Add session_id if provided (backward compatible)
        if session_id is not None:
            document['session_id'] = str(session_id)
        
        collection.insert_one(document)
        return True
    except Exception as e:
        logger.error(f"Error inserting active prediction: {e}")
        return False


def get_active_predictions(video_no: Optional[int] = None, user_id: Optional[str] = None, 
                          session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get active predictions (for frontend)
    
    Args:
        video_no: Optional video filter
        user_id: Optional user filter (for multi-user support)
        session_id: Optional session filter
    
    Returns:
        List of prediction dictionaries
    """
    try:
        collection = get_collection('active_predictions')
        query = {}
        
        # Build query with provided filters (backward compatible)
        if video_no is not None:
            query['video_no'] = video_no
        if user_id is not None:
            query['user_id'] = user_id
        if session_id is not None:
            query['session_id'] = session_id
        
        cursor = collection.find(query).sort('starttime', 1)
        return list(cursor)
    except Exception as e:
        logger.error(f"Error getting active predictions: {e}")
        return []


def clear_active_predictions(video_no: Optional[int] = None) -> bool:
    """
    Clear active predictions (called before video ends)
    
    Args:
        video_no: Optional - clear only for specific video
    
    Returns:
        bool: Success status
    """
    try:
        collection = get_collection('active_predictions')
        query = {'video_no': video_no} if video_no is not None else {}
        result = collection.delete_many(query)
        logger.info(f"🗑️  Cleared {result.deleted_count} active predictions")
        return True
    except Exception as e:
        logger.error(f"Error clearing active predictions: {e}")
        return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_all_data():
    """
    Clear all data from all collections (USE WITH CAUTION!)
    For testing/development only
    """
    try:
        collections = ['signals', 'video_starts', 'windowed_data', 
                      'change_scores', 'features', 'predictions', 'active_predictions']
        
        for coll_name in collections:
            collection = get_collection(coll_name)
            result = collection.delete_many({})
            logger.info(f"🗑️  Cleared {result.deleted_count} documents from {coll_name}")
        
        logger.info("✅ All data cleared!")
        return True
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        return False


def get_database_stats() -> Dict[str, Any]:
    """
    Get statistics about the database
    
    Returns:
        Dict with collection counts
    """
    try:
        stats = {}
        collections = ['signals', 'video_starts', 'windowed_data', 
                      'change_scores', 'features', 'predictions', 'active_predictions']
        
        for coll_name in collections:
            collection = get_collection(coll_name)
            count = collection.count_documents({})
            stats[coll_name] = count
        
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}


if __name__ == "__main__":
    """Test database operations"""
    print("\n" + "="*60)
    print("SURJA Database Models Test")
    print("="*60 + "\n")
    
    # Get database statistics
    stats = get_database_stats()
    print("📊 Database Statistics:")
    for collection, count in stats.items():
        print(f"   {collection}: {count} documents")
    
    print("\n✅ Database models loaded successfully!")

