import serial
import sys
import time
from datetime import datetime
import pytz
import os

# Get user number
user = int(input("Enter User No.: "))
print("Starting data collection...")

# Set up output filenames
start_time_unix = int(time.time())
# Use local directory instead of hardcoded path
output_dir = os.path.join(os.getcwd(), "raw_data", "Physiological_signals")
filename_base2 = os.path.join(output_dir, f"user{user}_physiological")
filename_base = f"signals_data_user{user}"
csv_path = f"{filename_base2}.csv"
txt_path = f"{filename_base}.txt"
bad_path = f"{filename_base}_bad.txt"

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

# Open files
file_csv = open(csv_path, "w")
file_txt = open(txt_path, "w")
bad_log = open(bad_path, "w")

# Connect to Arduino (update this if needed)
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
except serial.SerialException:
    print("❌ Could not open serial port /dev/ttyUSB0. Check your connection.")
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
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        timestamp_ms = int(time.time() * 1000)

        # Read serial data
        try:
            line = ser.readline().decode('utf-8', errors='replace').strip()
        except UnicodeDecodeError:
            bad_log.write(f"DecodeError: {line}\n")
            continue  # Skip malformed lines

        # Skip empty or partial lines
        if not line:
            continue

        parts = line.split(",")
        if len(parts) != 3:
            bad_log.write(f"Malformed (not 3 fields): {line}\n")
            continue

        try:
            arduino_millis = int(parts[0])
            gsr = int(parts[1])
            hr = int(parts[2])
        except ValueError:
            bad_log.write(f"Non-integer: {line}\n")
            continue

        # All checks passed, format and store
        row = f"{arduino_millis},{gsr},{hr},{timestamp_ms},{current_time}\n"
        # row = f"{gsr},{hr},{timestamp_ms},{current_time}\n"
        buff += row
        print(row.strip())

        # Save buffer to file every 5 seconds
        if (time.time() - start_time) >= save_interval:
            file_csv.write(buff)
            file_txt.write(buff)
            file_csv.flush()
            file_txt.flush()
            buff = ""
            start_time = time.time()

except KeyboardInterrupt:
    print("\n🛑 Data collection stopped by user.")

finally:
    # Close files safely
    file_csv.close()
    file_txt.close()
    bad_log.close()
    ser.close()
    print(f"\n✅ Data saved to:\n  {csv_path}\n  {txt_path}\n  ⚠️ Bad rows logged to: {bad_path}")
