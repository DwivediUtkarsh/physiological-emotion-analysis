#!/bin/bash

# Test script to simulate a video start event for main.py
# This creates a new timestamp file that main.py will detect

echo "🎬 Simulating Video Start Event..."
echo ""

# Get current timestamp in milliseconds
TIMESTAMP=$(date +%s%3N)

# Video ID (2 = 151 seconds video)
VIDEO_ID=2

# Create the video start file
echo "${TIMESTAMP},${VIDEO_ID}" > downloaded/start_times_test_${TIMESTAMP}.csv

echo "✅ Created: downloaded/start_times_test_${TIMESTAMP}.csv"
echo "   Timestamp: ${TIMESTAMP}"
echo "   Video ID: ${VIDEO_ID}"
echo ""
echo "📊 main.py should now detect this file and start processing!"
echo ""
echo "Watch the terminal where main.py is running for activity."




