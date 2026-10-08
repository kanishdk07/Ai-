#!/bin/bash

# Quick Start Script for Highway Accident Detection Backend
# This script helps set up and run the application

set -e

echo "🚨 Highway Accident Detection System - Backend Setup"
echo "===================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate 2>/dev/null
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your configuration:"
    echo "   - DATABASE_URL (PostgreSQL connection)"
    echo "   - SECRET_KEY (generate with: openssl rand -hex 32)"
    echo ""
    read -p "Press Enter after configuring .env to continue..."
else
    echo "✓ .env file exists"
fi
echo ""

# Create logs directory
mkdir -p logs
echo "✓ Logs directory ready"
echo ""

echo "===================================================="
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo ""
echo "1. Setup PostgreSQL database:"
echo "   createdb highway_accident_detection"
echo "   psql -d highway_accident_detection -c \"CREATE EXTENSION postgis;\""
echo ""
echo "2. Create admin user:"
echo "   python -m app.scripts.create_admin"
echo ""
echo "3. Run the application:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "4. Access the API:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/api/v1/admin/health"
echo ""
echo "===================================================="
