# JobJugaad

This repository contains the initial skeleton for the JobJugaad AI-powered campus placement platform.

## Frontend
- Located in the `frontend/` directory.
- React + Vite + Tailwind CSS.
- Exposes a simple health‑check page that calls the backend `/health` endpoint.

## Backend
- Located in the `backend/` directory.
- FastAPI server with a single `GET /health` endpoint.

## Development
```bash
# Frontend
cd frontend
npm install   # install dependencies
npm run dev   # start Vite dev server (http://localhost:5173)

# Backend
cd ../backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000
```

## Deployment
- Frontend will be deployed to Vercel.
- Backend will be deployed to Render as a Web Service.
- After deployment, set the `VITE_API_URL` environment variable in Vercel to the Render backend URL.
