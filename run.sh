#!/bin/bash

# IntelliK8sBot Quick Start Script
# This script sets up and runs IntelliK8sBot locally

set -e

echo "============================================"
echo "   IntelliK8sBot - Quick Start"
echo "============================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

echo ""
echo "============================================"
echo "   Setup Complete!"
echo "============================================"
echo ""
echo "Choose how to run IntelliK8sBot:"
echo ""
echo "  1. Web UI + API Server:"
echo "     python -m uvicorn app.main:app --reload"
echo "     Then open: http://localhost:8000"
echo ""
echo "  2. CLI Interactive Mode:"
echo "     python cli.py chat"
echo ""
echo "  3. CLI Commands:"
echo "     python cli.py --help"
echo ""
echo "============================================"
echo ""

# Ask user how to proceed
read -p "Start the web server now? [Y/n]: " choice
case "$choice" in 
    n|N ) 
        echo "You can start later with: source venv/bin/activate && python -m uvicorn app.main:app --reload"
        ;;
    * ) 
        echo "Starting server..."
        python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
esac
