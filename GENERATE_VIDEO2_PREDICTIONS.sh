#!/bin/bash
# Generate predictions for Video 2

echo "🎬 Generating Predictions for Video 2"
echo "======================================"
echo ""

# Step 1: Check signals.py is running
echo "Step 1: Checking if signals.py is collecting data..."
if [ ! -f "signals_data.csv" ]; then
    echo "❌ ERROR: signals_data.csv not found!"
    echo "   Please start signals.py first:"
    echo "   source venv_signals/bin/activate && python signals.py /dev/ttyUSB0"
    exit 1
fi

SIGNAL_COUNT=$(wc -l < signals_data.csv)
echo "✅ Found signals_data.csv with $SIGNAL_COUNT lines"

# Step 2: Check last signal timestamp
LAST_TIMESTAMP=$(tail -1 signals_data.csv | cut -d',' -f4)
CURRENT_TIME=$(date +%s%3N)
TIME_DIFF=$((CURRENT_TIME - LAST_TIMESTAMP))

echo ""
echo "Step 2: Checking signal freshness..."
echo "   Last signal: $LAST_TIMESTAMP"
echo "   Current time: $CURRENT_TIME"
echo "   Age: $((TIME_DIFF / 1000)) seconds"

if [ $TIME_DIFF -gt 60000 ]; then
    echo "⚠️  WARNING: Signals are more than 60 seconds old!"
    echo "   Consider restarting signals.py for fresh data"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 3: Trigger video start API
echo ""
echo "Step 3: Triggering video processing for Video 2..."
TIMESTAMP=$(date +%s%3N)
SESSION_ID="video2_$(date +%s)"

RESPONSE=$(curl -s -X POST http://localhost:5000/api/video/start \
  -H "Content-Type: application/json" \
  -d "{
    \"video_id\": 2,
    \"timestamp\": $TIMESTAMP,
    \"user_id\": \"user111\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "$RESPONSE" | python3 -m json.tool

# Check if successful
if echo "$RESPONSE" | grep -q '"status": "success"'; then
    echo ""
    echo "✅ Processing started successfully!"
    echo ""
    echo "⏳ Video 2 duration: 151 seconds (2 minutes 31 seconds)"
    echo "   Processing will take approximately 3 minutes total"
    echo ""
    echo "📊 Monitor progress:"
    echo "   curl http://localhost:5000/api/video/sessions/active"
    echo ""
    echo "🔍 Check predictions after completion:"
    echo "   mongosh surja_db --eval \"db.predictions.countDocuments({video_no: 2})\""
    echo ""
    echo "⏰ Check back in 3 minutes!"
else
    echo ""
    echo "❌ Failed to start processing!"
    echo "   Check if api/server.py is running"
fi
