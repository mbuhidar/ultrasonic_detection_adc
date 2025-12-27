#!/bin/bash
# Quick Start Script for Ultrasonic Detection System

echo "Ultrasonic Detection System - Quick Start"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r ../requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Available commands:"
echo "  python data_collector.py          - Start data collection"
echo "  python data_collector.py -s 20    - Collect 20 samples per trigger"
echo "  python realtime_viewer.py         - View data in real-time"
echo "  python data_analyzer.py <file>    - Analyze collected data"
echo ""
echo "Press Ctrl+C to stop any running script"
echo ""

# Keep shell active
exec bash
