#!/bin/bash
set -e

echo "Setting up ResumeForge..."

cd "$(dirname "$0")/.."

if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env and add your API keys before starting!"
fi

if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "Virtual environment already exists"
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "Frontend dependencies already installed"
fi

mkdir -p data/uploads data/exports

echo ""
echo "Setup complete!"
echo ""
echo "Start the backend:"
echo "  cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo ""
echo "Start the frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173"
echo ""
echo "Or use Docker:"
echo "  docker compose up --build"
