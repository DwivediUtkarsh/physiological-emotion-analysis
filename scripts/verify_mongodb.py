#!/usr/bin/env python3
"""
MongoDB Verification Script

This script provides an easy way to verify data in MongoDB
without using the mongo shell.
"""

import sys
import os
from datetime import datetime
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_models import (
    get_collection,
    get_database_stats,
    get_active_predictions,
    get_latest_video_start
)
from db_config import get_db


def print_section_header(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def show_database_stats():
    """Show overall database statistics"""
    print_section_header("📊 DATABASE STATISTICS")
    
    stats = get_database_stats()
    table_data = []
    
    for collection, count in stats.items():
        table_data.append([
            collection,
            f"{count:,}"
        ])
    
    print(tabulate(table_data, 
                   headers=['Collection', 'Documents'],
                   tablefmt='grid'))


def show_user_stats():
    """Show statistics by user"""
    print_section_header("👥 USER STATISTICS")
    
    collection = get_collection('predictions')
    
    # Check if there are any users
    sample = collection.find_one({'user_id': {'$exists': True}})
    if not sample:
        print("⚠️  No user_id field found in data. Run with old data or data needs migration.")
        return
    
    # Aggregate by user
    pipeline = [
        {'$match': {'user_id': {'$exists': True}}},
        {'$group': {
            '_id': '$user_id',
            'total_predictions': {'$sum': 1},
            'videos': {'$addToSet': '$video_no'}
        }},
        {'$sort': {'_id': 1}}
    ]
    
    user_stats = list(collection.aggregate(pipeline))
    
    if not user_stats:
        print("No user data found.")
        return
    
    table_data = []
    for user in user_stats:
        table_data.append([
            user['_id'],
            user['total_predictions'],
            len(user['videos']),
            ', '.join(map(str, sorted(user['videos'])))
        ])
    
    print(tabulate(table_data,
                   headers=['User ID', 'Predictions', 'Videos', 'Video IDs'],
                   tablefmt='grid'))
    
    # Also show signals per user
    signals_collection = get_collection('signals')
    signals_pipeline = [
        {'$match': {'user_id': {'$exists': True}}},
        {'$group': {
            '_id': '$user_id',
            'signal_count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    
    signals_stats = list(signals_collection.aggregate(signals_pipeline))
    
    if signals_stats:
        print("\n📡 Signals per user:")
        signal_table = []
        for user in signals_stats:
            signal_table.append([
                user['_id'],
                f"{user['signal_count']:,}"
            ])
        
        print(tabulate(signal_table,
                       headers=['User ID', 'Signal Count'],
                       tablefmt='grid'))


def show_video_starts():
    """Show all video start records"""
    print_section_header("📹 VIDEO START RECORDS")
    
    collection = get_collection('video_starts')
    videos = list(collection.find().sort('timestamp', -1).limit(10))
    
    if not videos:
        print("No video start records found.")
        return
    
    table_data = []
    for video in videos:
        timestamp = video.get('timestamp', 0)
        dt = datetime.fromtimestamp(timestamp / 1000)
        
        table_data.append([
            video.get('video_id', 'N/A'),
            video.get('user_id', 'N/A'),
            video.get('session_id', 'N/A')[:20] + '...' if video.get('session_id') and len(video.get('session_id', '')) > 20 else video.get('session_id', 'N/A'),
            dt.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    print(tabulate(table_data,
                   headers=['Video ID', 'User ID', 'Session ID', 'DateTime'],
                   tablefmt='grid'))


def show_predictions_by_video(video_id: int = None):
    """Show predictions for a specific video or all videos"""
    if video_id:
        print_section_header(f"🤖 PREDICTIONS FOR VIDEO {video_id}")
        query = {'video_no': video_id}
    else:
        print_section_header("🤖 ALL PREDICTIONS (Last 20)")
        query = {}
    
    collection = get_collection('predictions')
    predictions = list(collection.find(query).sort('starttime', 1).limit(20))
    
    if not predictions:
        print(f"No predictions found{f' for video {video_id}' if video_id else ''}.")
        return
    
    table_data = []
    emotion_map = {
        'HH': 'Happy',
        'HL': 'Neutral',
        'LH': 'Angry',
        'LL': 'Sad'
    }
    
    for pred in predictions:
        timestamp = pred.get('starttime', 0)
        dt = datetime.fromtimestamp(timestamp / 1000)
        probe = pred.get('probe', 'N/A')
        
        table_data.append([
            pred.get('video_no', 'N/A'),
            pred.get('user_id', 'N/A'),
            dt.strftime('%H:%M:%S'),
            probe,
            emotion_map.get(probe, 'Unknown')
        ])
    
    print(tabulate(table_data,
                   headers=['Video', 'User', 'Time', 'Probe', 'Emotion'],
                   tablefmt='grid'))


def show_active_predictions():
    """Show currently active predictions"""
    print_section_header("⚡ ACTIVE PREDICTIONS (For Frontend)")
    
    predictions = get_active_predictions()
    
    if not predictions:
        print("No active predictions found.")
        return
    
    table_data = []
    emotion_map = {
        'HH': 'Happy',
        'HL': 'Neutral',
        'LH': 'Angry',
        'LL': 'Sad'
    }
    
    for pred in predictions[:20]:  # Show first 20
        timestamp = pred.get('starttime', 0)
        dt = datetime.fromtimestamp(timestamp / 1000)
        probe = pred.get('probe', 'N/A')
        
        table_data.append([
            pred.get('video_no', 'N/A'),
            pred.get('user_id', 'N/A'),
            dt.strftime('%H:%M:%S'),
            probe,
            emotion_map.get(probe, 'Unknown')
        ])
    
    print(tabulate(table_data,
                   headers=['Video', 'User', 'Time', 'Probe', 'Emotion'],
                   tablefmt='grid'))


def show_signals_sample():
    """Show sample signal data"""
    print_section_header("📡 SIGNAL DATA (Sample - Last 10)")
    
    collection = get_collection('signals')
    signals = list(collection.find().sort('timestamp', -1).limit(10))
    
    if not signals:
        print("No signal data found.")
        return
    
    table_data = []
    for signal in signals:
        table_data.append([
            signal.get('user_id', 'N/A'),
            signal.get('video_id', 'N/A'),
            signal.get('time_series', 'N/A'),
            f"{signal.get('gsr', 'N/A'):.2f}" if isinstance(signal.get('gsr'), (int, float)) else 'N/A',
            f"{signal.get('hr', 'N/A'):.2f}" if isinstance(signal.get('hr'), (int, float)) else 'N/A',
            signal.get('datetime', 'N/A')[:19] if signal.get('datetime') else 'N/A'
        ])
    
    print(tabulate(table_data,
                   headers=['User', 'Video', 'Time Series', 'GSR', 'HR', 'DateTime'],
                   tablefmt='grid'))


def show_features():
    """Show feature data"""
    print_section_header("🔬 FEATURE DATA (Last 10)")
    
    collection = get_collection('features')
    features = list(collection.find().sort('start_time', -1).limit(10))
    
    if not features:
        print("No feature data found.")
        return
    
    table_data = []
    for feature in features:
        table_data.append([
            feature.get('video_no', 'N/A'),
            f"{feature.get('valence', 'N/A')}",
            f"{feature.get('arousal', 'N/A')}",
            feature.get('start_time', 'N/A')
        ])
    
    print(tabulate(table_data,
                   headers=['Video', 'Valence', 'Arousal', 'Start Time'],
                   tablefmt='grid'))


def interactive_menu():
    """Interactive menu for data verification"""
    while True:
        print("\n" + "="*70)
        print("  🗄️  MONGODB DATA VERIFICATION TOOL")
        print("="*70)
        print("\nChoose an option:")
        print("  1. Show Database Statistics")
        print("  2. Show User Statistics")
        print("  3. Show Video Start Records")
        print("  4. Show All Predictions (Last 20)")
        print("  5. Show Predictions for Specific Video")
        print("  6. Show Active Predictions")
        print("  7. Show Signal Data (Sample)")
        print("  8. Show Feature Data")
        print("  9. Show Everything")
        print("  0. Exit")
        
        choice = input("\nEnter choice (0-9): ").strip()
        
        if choice == '1':
            show_database_stats()
        elif choice == '2':
            show_user_stats()
        elif choice == '3':
            show_video_starts()
        elif choice == '4':
            show_predictions_by_video()
        elif choice == '5':
            video_id = input("Enter Video ID (1-4): ").strip()
            try:
                show_predictions_by_video(int(video_id))
            except ValueError:
                print("❌ Invalid video ID. Please enter a number.")
        elif choice == '6':
            show_active_predictions()
        elif choice == '7':
            show_signals_sample()
        elif choice == '8':
            show_features()
        elif choice == '9':
            show_database_stats()
            show_user_stats()
            show_video_starts()
            show_predictions_by_video()
            show_active_predictions()
            show_signals_sample()
            show_features()
        elif choice == '0':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        # Check connection
        db = get_db()
        if db is None:
            print("❌ Failed to connect to MongoDB")
            print("\n💡 Make sure MongoDB is running:")
            print("   mongod --dbpath /data/db --fork")
            sys.exit(1)
        
        print("✅ Connected to MongoDB")
        
        # Check if running with arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--stats':
                show_database_stats()
            elif sys.argv[1] == '--users':
                show_user_stats()
            elif sys.argv[1] == '--video':
                if len(sys.argv) > 2:
                    show_predictions_by_video(int(sys.argv[2]))
                else:
                    print("Usage: python verify_mongodb.py --video <video_id>")
            elif sys.argv[1] == '--all':
                show_database_stats()
                show_user_stats()
                show_video_starts()
                show_predictions_by_video()
                show_active_predictions()
                show_signals_sample()
                show_features()
            else:
                print("Usage:")
                print("  python verify_mongodb.py              # Interactive mode")
                print("  python verify_mongodb.py --stats      # Show statistics only")
                print("  python verify_mongodb.py --users      # Show user statistics")
                print("  python verify_mongodb.py --video 2    # Show video 2 predictions")
                print("  python verify_mongodb.py --all        # Show everything")
        else:
            # Interactive mode
            interactive_menu()
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

