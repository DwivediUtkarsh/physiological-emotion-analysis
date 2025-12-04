#!/bin/bash

# SURJA Complete System Startup Script
# This script helps you start all components of the SURJA system

set -e  # Exit on error

echo "🚀 SURJA System Startup Helper"
echo "================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

echo "📋 Pre-flight Checks..."
echo ""

# Check Python
if command_exists python3; then
    echo -e "${GREEN}✅${NC} Python3 found: $(python3 --version)"
else
    echo -e "${RED}❌${NC} Python3 not found. Please install Python 3.12+"
    exit 1
fi

# Check Node.js
if command_exists node; then
    echo -e "${GREEN}✅${NC} Node.js found: $(node --version)"
else
    echo -e "${RED}❌${NC} Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check MongoDB
if command_exists mongod; then
    echo -e "${GREEN}✅${NC} MongoDB found: $(mongod --version | head -n 1)"
else
    echo -e "${RED}❌${NC} MongoDB not found. Please install MongoDB"
    exit 1
fi

# Check virtual environments
if [ -d "venv_db" ]; then
    echo -e "${GREEN}✅${NC} venv_db found"
else
    echo -e "${YELLOW}⚠️${NC}  venv_db not found. Run: python3 -m venv venv_db"
fi

if [ -d "venv_signals" ]; then
    echo -e "${GREEN}✅${NC} venv_signals found"
else
    echo -e "${YELLOW}⚠️${NC}  venv_signals not found. Run: python3 -m venv venv_signals"
fi

echo ""
echo "🔍 Checking Ports..."
echo ""

# Check if ports are available
if port_in_use 27017; then
    echo -e "${GREEN}✅${NC} MongoDB already running on port 27017"
else
    echo -e "${YELLOW}⚠️${NC}  MongoDB not running on port 27017"
fi

if port_in_use 5000; then
    echo -e "${YELLOW}⚠️${NC}  Port 5000 (Backend API) is already in use"
else
    echo -e "${GREEN}✅${NC} Port 5000 available"
fi

if port_in_use 8000; then
    echo -e "${YELLOW}⚠️${NC}  Port 8000 (Annotations API) is already in use"
else
    echo -e "${GREEN}✅${NC} Port 8000 available"
fi

if port_in_use 5173; then
    echo -e "${YELLOW}⚠️${NC}  Port 5173 (Frontend) is already in use"
else
    echo -e "${GREEN}✅${NC} Port 5173 available"
fi

echo ""
echo "================================"
echo ""
echo "📝 STARTUP INSTRUCTIONS:"
echo ""
echo "You need to open 6 separate terminal windows and run these commands:"
echo ""

echo -e "${GREEN}TERMINAL 1: MongoDB${NC}"
echo "  cd $(pwd)"
echo "  sudo mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork"
echo ""

echo -e "${GREEN}TERMINAL 2: Hardware Signals (Optional)${NC}"
echo "  cd $(pwd)"
echo "  source venv_signals/bin/activate"
echo "  python signals.py /dev/ttyUSB0"
echo "  # Skip this if no hardware connected"
echo ""

echo -e "${GREEN}TERMINAL 3: Backend Processing Pipeline${NC}"
echo "  cd $(pwd)"
echo "  source venv_db/bin/activate"
echo "  python main.py"
echo ""

echo -e "${GREEN}TERMINAL 4: Backend API Server${NC}"
echo "  cd $(pwd)"
echo "  source venv_db/bin/activate"
echo "  python api/server.py"
echo ""

echo -e "${GREEN}TERMINAL 5: Annotations Backend${NC}"
echo "  cd $(pwd)/frontend/annotations-backend"
echo "  source ../../venv_db/bin/activate"
echo "  uvicorn app_fastapi:app --reload --port 8000"
echo ""

echo -e "${GREEN}TERMINAL 6: Frontend UI${NC}"
echo "  cd $(pwd)/frontend"
echo "  npm run dev"
echo ""

echo "================================"
echo ""
echo "🌐 Once all services are running, open:"
echo "   http://localhost:5173"
echo ""
echo "📚 For detailed instructions, see:"
echo "   COMPLETE_STARTUP_GUIDE.md"
echo ""

# Ask if user wants to start MongoDB now
read -p "Do you want to start MongoDB now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting MongoDB..."
    sudo mongod --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork
    echo -e "${GREEN}✅${NC} MongoDB started!"
    echo ""
    echo "Now open 5 more terminals and follow the instructions above."
else
    echo "Skipping MongoDB startup."
    echo "Follow the instructions above to start all services manually."
fi

echo ""
echo "🎉 Happy emotion analyzing!"




