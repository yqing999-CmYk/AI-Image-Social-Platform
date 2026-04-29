#!/usr/bin/env bash
# Start both frontend and backend for local development
# Usage: bash dev-start.sh

set -e

# Backend — FastAPI on port 8000
echo "[backend] Starting FastAPI on http://localhost:8000 ..."
cd backend
env -u PYTHONHOME -u PYTHONPATH uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend — Next.js on port 3000
echo "[frontend] Starting Next.js on http://localhost:3000 ..."
cd frontend
cp -n .env.local.example .env.local 2>/dev/null || true
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Services running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
