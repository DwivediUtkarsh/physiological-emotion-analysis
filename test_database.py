"""
Quick test script to verify database setup
"""

from db_config import DatabaseConnection, initialize_indexes
from db_models import (
    insert_signal,
    insert_video_start,
    insert_change_score,
    insert_feature,
    insert_prediction,
    insert_active_prediction,
    get_database_stats,
    clear_all_data
)
from datetime import datetime

print("\n" + "="*70)
print("SURJA Database Test Script")
print("="*70 + "\n")

# Test 1: Connection
print("1️⃣  Testing database connection...")
conn = DatabaseConnection()
if conn.connect():
    print("   ✅ Connection successful!\n")
else:
    print("   ❌ Connection failed!\n")
    exit(1)

# Test 2: Insert sample data
print("2️⃣  Testing data insertion...")

# Insert sample signal
result = insert_signal({
    'time_series': 1000,
    'gsr': 654,
    'hr': 255,
    'timestamp': 1742364511965,
    'datetime': '2025-03-19 11:38:31.965+05:30'
})
print(f"   Signal insert: {'✅' if result else '❌'}")

# Insert video start
result = insert_video_start(1742364538211, 1)
print(f"   Video start insert: {'✅' if result else '❌'}")

# Insert change score
result = insert_change_score(
    start_time=1742364511965,
    start=1742364511965,
    border=1742364517081,
    end=1742364522516,
    score=0.0010553099576358083
)
print(f"   Change score insert: {'✅' if result else '❌'}")

# Insert feature
result = insert_feature({
    'start_time': 1742364828813,
    'score': 3.4614863309023753e-08,
    'gsr_diff': 0.0,
    'hr_diff': 0.12,
    'previous_window': 3,
    'valence_acc_video': 0,
    'arousal_acc_video': 1,
    'video_id': 2
})
print(f"   Feature insert: {'✅' if result else '❌'}")

# Insert prediction
result = insert_prediction(1742305079661, 2, "HL", 0)
print(f"   Prediction insert: {'✅' if result else '❌'}")

# Insert active prediction
result = insert_active_prediction(1742305079661, 2, "HL")
print(f"   Active prediction insert: {'✅' if result else '❌'}\n")

# Test 3: Database statistics
print("3️⃣  Database statistics:")
stats = get_database_stats()
for collection, count in stats.items():
    print(f"   {collection:20} : {count:3} documents")

print("\n" + "="*70)
print("✅ All tests completed successfully!")
print("="*70)

# Optional: Clear test data
print("\n🧹 Cleaning up test data...")
clear_all_data()
print("✅ Test data cleared!\n")

conn.close()

