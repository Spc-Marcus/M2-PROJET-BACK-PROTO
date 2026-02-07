#!/bin/bash
# Startup script for Duobingo API

echo "🚀 Starting Duobingo API..."
echo ""

# Set PYTHONPATH
export PYTHONPATH=.

# Seed database
echo "📊 Seeding database with test users..."
python app/utils/seed.py
echo ""

# Start the server
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
