# IntelResponse – Incident Intelligence Platform

## Problem
IntelResponse is an AI-powered incident intelligence system that helps security teams rapidly triage, correlate, and respond to cybersecurity incidents.

## Setup

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Demo Flow
1. Start backend server
2. Start frontend dev server
3. Submit sample incidents via the UI
4. View extracted IOCs, risk scores, and similar incident clusters

<!-- TODO: Add architecture diagram -->
<!-- TODO: Add screenshots -->
