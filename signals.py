import serial
import sys
import time
from datetime import datetime
import pytz
import os

# MongoDB integration - dual write (CSV + DB)
try:
    from db_models import insert_signals_bulk, get_latest_video_start
    DB_ENABLED = True
    print("✅ MongoDB integration enabled")
except ImportError as e:
    DB_ENABLED = False
    print(f"⚠️  MongoDB not available: {e}. Using CSV only.")

def get_current_session_info():
    """
    Get current session info from latest video start.
    Returns tuple: (user_id, video_id, session_id) or (None, None, None)
    """
    if not DB_ENABLED:
        return None, None, None
    
    try:
        latest_video = get_latest_video_start()
        if latest_video:
            return (
                latest_video.get('user_id'),
                latest_video.get('video_id'),
                latest_video.get('session_id')
            )
    except Exception as e:
        print(f"⚠️  Could not get session info: {e}")
    
    return None, None, None

# Check command line arguments
if len(sys.argv) != 2:
    print("  Usage: python signals.py <PORT>\n  Example (WSL): python signals.py /dev/ttyUSB0\n  Example (Windows): python signals.py COM3\n")
    exit(-1)

# Get user number for file organization
try:
    user = int(input("Enter User No.: "))
    print(f"Starting data collection for User {user}...")
except ValueError:
    print("❌ Invalid user number. Using default (0).")
    user = 0

# Set up output paths
currtime = time.time()
file_prefix = str(currtime)
output_dir = os.path.join(os.getcwd(), "raw_data", "Physiological_signals")
os.makedirs(output_dir, exist_ok=True)

# File paths
csv_path = os.path.join(output_dir, f"user{user}_physiological.csv")
txt_path = f"signals_data_user{user}.txt"
bad_path = f"signals_data_user{user}_bad.txt"
# CRITICAL: shared CSV that backend pipeline reads
shared_csv_path = os.path.join(os.getcwd(), "signals_data.csv")

# Open files
file_csv = open(csv_path, "w")
file_txt = open(txt_path, "w")
bad_log = open(bad_path, "w")
# Shared CSV in append mode so it accumulates across runs
file_shared = open(shared_csv_path, "a")

# Connect to serial device
try:
    ser = serial.Serial(sys.argv[1], 9600, timeout=1)
    print(f"✅ Connected to {sys.argv[1]}")
except serial.SerialException as e:
    print(f"❌ Could not open serial port {sys.argv[1]}: {e}")
    file_csv.close()
    file_txt.close()
    bad_log.close()
    sys.exit(1)

# Allow time for Arduino to reset
time.sleep(2)

# Setup logging
buff = ""
save_interval = 5  # seconds
start_time = time.time()

try:
    while True:
        # Timestamp
        ist_timezone = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist_timezone)
        timestamp_ms = int(time.time() * 1000)

        # Read serial data with error handling
        try:
            line = ser.readline().decode('utf-8', errors='replace').strip()
        except UnicodeDecodeError as e:
            bad_log.write(f"DecodeError at {timestamp_ms}: {e}\n")
            continue

        # Skip empty lines
        if not line:
            continue

        # Parse Arduino data: expected format "arduino_millis,gsr,hr"
        parts = line.split(",")
        if len(parts) != 3:
            bad_log.write(f"Malformed (not 3 fields) at {timestamp_ms}: {line}\n")
            continue

        try:
            arduino_millis = int(parts[0])
            gsr = int(parts[1])
            hr = int(parts[2])
        except ValueError:
            bad_log.write(f"Non-integer values at {timestamp_ms}: {line}\n")
            continue

        # All checks passed, format and store
        row = f"{arduino_millis},{gsr},{hr},{timestamp_ms},{current_time}\n"
        buff += row
        print(row.strip())

        # Save buffer to files and MongoDB every 5 seconds
        elapsed_time = time.time() - start_time
        if elapsed_time >= save_interval:
            # DUAL WRITE: CSV files
            file_csv.write(buff)
            file_txt.write(buff)
            file_shared.write(buff)  # shared CSV for backend pipeline
            file_csv.flush()
            file_txt.flush()
            file_shared.flush()
            
            # DUAL WRITE: MongoDB (new functionality)
            if DB_ENABLED and buff.strip():
                try:
                    # Get current session info (user_id, video_id, session_id)
                    current_user_id, current_video_id, current_session_id = get_current_session_info()
                    
                    # Parse buffer data for MongoDB insertion
                    signal_data = []
                    for line in buff.strip().split('\n'):
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) >= 5:
                                doc = {
                                    'time_series': int(parts[0]),
                                    'gsr': int(parts[1]),
                                    'hr': int(parts[2]),
                                    'timestamp': int(parts[3]),
                                    'datetime': parts[4]
                                }
                                
                                # Add session context if available (for multi-user support)
                                if current_user_id:
                                    doc['user_id'] = str(current_user_id)
                                if current_video_id:
                                    doc['video_id'] = int(current_video_id)
                                if current_session_id:
                                    doc['session_id'] = str(current_session_id)
                                
                                signal_data.append(doc)
                    
                    # Bulk insert into MongoDB
                    if signal_data:
                        insert_signals_bulk(signal_data)
                        log_msg = f"📊 Inserted {len(signal_data)} signals to MongoDB"
                        if current_user_id:
                            log_msg += f" (user: {current_user_id}, video: {current_video_id})"
                        print(log_msg)
                except Exception as e:
                    print(f"⚠️  MongoDB insert failed: {e}. CSV backup intact.")
            
            buff = ""
            start_time = time.time()

except KeyboardInterrupt:
    print("\n🛑 Data collection stopped by user.")

finally:
    # Close files and serial connection safely
    file_csv.close()
    file_txt.close()
    file_shared.close()
    bad_log.close()
    ser.close()
    print(f"\n✅ Data saved to:\n  CSV: {csv_path}\n  TXT: {txt_path}\n  Shared: {shared_csv_path}\n  ⚠️ Bad rows logged to: {bad_path}")