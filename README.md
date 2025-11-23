# Project Smart Trade - Walkthrough

This guide explains how to run the full-stack Smart Trade application.

## Prerequisites
- Python 3.8+
- Node.js 16+
- (Optional) Ollama running locally for real AI inference
- (Optional) Alpaca Paper Trading API Keys

## 1. Backend Setup
The backend runs on FastAPI and handles the API requests.

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*The API will be available at http://localhost:8000*

## 2. Frontend Setup
The frontend is a React app showing the dashboard.

```bash
cd frontend
npm install
npm run dev
```
*The Dashboard will be available at http://localhost:5173*

## 3. AI Agent Setup
The AI agent runs as a standalone script that simulates trading decisions.

```bash
cd ai_agent
pip install -r requirements.txt
python agent.py
```

## Features
- **Dashboard**: Real-time portfolio value, cash balance, and active positions.
- **Trade Logs**: View recent trades executed by the agent.
- **Agent Simulation**: The `agent.py` script simulates RAG-based decision making and executes trades (mocked) via the backend.
- **RAG Integration**: The agent loads strategy documents into ChromaDB (if available) to inform decisions.

## Notes
- If `chromadb` is not installed or fails (e.g. due to C++ build tools), the agent will fallback to a mocked RAG response.
- The backend currently mocks Alpaca data. To use real data, update `backend/main.py` with your Alpaca API keys.
