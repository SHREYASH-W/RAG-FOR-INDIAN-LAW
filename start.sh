#!/bin/bash

echo "Starting setup for Replit..."

# 1. Install backend dependencies
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# 2. Start FastAPI backend in the background
echo "Starting FastAPI backend..."
cd backend
# Replit uses 0.0.0.0 and dynamically binds, but we bind to 127.0.0.1 
# so Next.js can proxy it and Replit exposes the Next.js app to the world.
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
cd ..

# 3. Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install

# 4. Start Next.js frontend
echo "Starting Next.js frontend..."
# Replit looks for the first exposed port, which Next.js will use (default 3000)
# We use host 0.0.0.0 to expose it to Replit's proxy
npm run dev -- -H 0.0.0.0
