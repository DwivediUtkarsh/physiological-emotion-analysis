#!/usr/bin/env python3
"""
Migration Script: Transfer Test Data to MongoDB

This script creates sample prediction data in MongoDB for testing purposes.
It simulates what the backend would create when processing videos.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_models import (
    insert_signals_bulk,
    insert_video_start,
    insert_feature,
    insert_prediction,
    insert_active_prediction,
    get_database_stats
)
from db_config import get_db

def create_sample_signals(video_id: int, start_timestamp: int, duration_seconds: int, 
                         user_id: str = None, session_id: str = None):
    """
    Create sample signal data for a video.
    Simulates GSR and HR readings every second.
    """
    print(f"\n📊 Creating sample signals for video {video_id}...")
    
    signals = []
    for i in range(duration_seconds):
        timestamp = start_timestamp + (i * 1000)  # Milliseconds
        
        # Simulate realistic GSR (200-300) and HR (60-90) values
        gsr = 250 + (i % 50)
        hr = 70 + (i % 20)
        
        signal_doc = {
            'time_series': i + 1,
            'gsr': gsr,
            'hr': hr,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add user context if provided
        if user_id:
            signal_doc['user_id'] = user_id
        if video_id:
            signal_doc['video_id'] = video_id
        if session_id:
            signal_doc['session_id'] = session_id
        
        signals.append(signal_doc)
    
    # Insert in batches
    batch_size = 100
    for i in range(0, len(signals), batch_size):
        batch = signals[i:i+batch_size]
        insert_signals_bulk(batch)
    
    log_msg = f"✅ Inserted {len(signals)} signal readings"
    if user_id:
        log_msg += f" for user {user_id}"
    print(log_msg)


def create_sample_predictions(video_id: int, start_timestamp: int, duration_seconds: int,
                            user_id: str = None, session_id: str = None):
    """
    Create sample prediction data for a video.
    Creates predictions every 5 seconds with different emotion states.
    """
    print(f"\n🤖 Creating sample predictions for video {video_id}...")
    
    # Emotion pattern simulation (cycles through different states)
    emotion_pattern = ['HH', 'HL', 'HH', 'LH', 'HL', 'LL', 'LH', 'HH']
    
    predictions = []
    segment_count = duration_seconds // 5
    
    for i in range(segment_count):
        timestamp = start_timestamp + (i * 5000)  # Every 5 seconds
        probe = emotion_pattern[i % len(emotion_pattern)]
        
        # Insert to permanent predictions with user context
        insert_prediction(timestamp, video_id, probe, cluster_id=0, user_id=user_id, session_id=session_id)
        
        # Also insert to active predictions (for frontend)
        insert_active_prediction(timestamp, video_id, probe, user_id=user_id, session_id=session_id)
        
        predictions.append({'timestamp': timestamp, 'probe': probe})
    
    log_msg = f"✅ Inserted {len(predictions)} predictions"
    if user_id:
        log_msg += f" for user {user_id}"
    print(log_msg)
    return predictions


def create_sample_video_data():
    """
    Create complete sample data for testing.
    """
    print("╔════════════════════════════════════════════════╗")
    print("║   MongoDB Test Data Migration Script          ║")
    print("╚════════════════════════════════════════════════╝\n")
    
    # Check database connection
    db = get_db()
    if db is None:
        print("❌ Failed to connect to MongoDB")
        return False
    
    print("✅ Connected to MongoDB\n")
    
    # Video configurations (matching backend)
    videos = [
        {'id': 1, 'duration': 180, 'name': 'Video 1 (3:00)'},
        {'id': 2, 'duration': 151, 'name': 'Video 2 (2:31)'},
        {'id': 3, 'duration': 160, 'name': 'Video 3 (2:40)'},
        {'id': 4, 'duration': 117, 'name': 'Video 4 (1:57)'}
    ]
    
    # Base timestamp (simulate videos played 1 hour ago)
    base_timestamp = int((datetime.now().timestamp() - 3600) * 1000)
    
    # Create data for multiple test users
    test_users = ['user1', 'user2']
    
    for user_id in test_users:
        print(f"\n{'🔵'*25}")
        print(f"Creating data for user: {user_id}")
        print(f"{'🔵'*25}")
        
        for video in videos:
            video_id = video['id']
            duration = video['duration']
            video_name = video['name']
            
            # Calculate timestamp for this video (spaced 5 minutes apart, different per user)
            user_offset = test_users.index(user_id) * 7200000  # 2 hours apart per user
            video_timestamp = base_timestamp + user_offset + (video_id * 300000)
            session_id = f"{user_id}_{video_id}_{video_timestamp}"
            
            print(f"\n{'='*50}")
            print(f"Processing: {video_name}")
            print(f"Video ID: {video_id}")
            print(f"User ID: {user_id}")
            print(f"Session ID: {session_id}")
            print(f"Duration: {duration}s")
            print(f"Timestamp: {video_timestamp}")
            print(f"{'='*50}")
            
            # 1. Record video start with user context
            print("\n📹 Recording video start...")
            insert_video_start(video_timestamp, video_id, user_id, session_id)
            print(f"✅ Video start recorded for {user_id}")
            
            # 2. Create sample signals with user context
            create_sample_signals(video_id, video_timestamp, duration, user_id, session_id)
            
            # 3. Create sample predictions with user context
            predictions = create_sample_predictions(video_id, video_timestamp, duration, user_id, session_id)
            
            print(f"\n✨ Completed {video_name} for {user_id}")
    
    # Show final statistics
    print("\n" + "="*50)
    print("📊 FINAL DATABASE STATISTICS")
    print("="*50 + "\n")
    
    stats = get_database_stats()
    for collection, count in stats.items():
        print(f"{collection:25} {count:>6,} documents")
    
    print("\n✅ Migration complete!")
    print("\n💡 To verify data in MongoDB, run:")
    print("   mongosh surja_db")
    print("   db.predictions.find({video_no: 2}).limit(5)")
    
    return True


if __name__ == "__main__":
    try:
        success = create_sample_video_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

