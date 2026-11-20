# OmniPulse — Real-Time Infrastructure Monitor

A full-stack telemetry dashboard that streams real-time server metrics via WebSockets with a high-performance React frontend.

## Architecture

**Backend:** Django + Channels + Redis  
**Frontend:** Next.js 14 + Recharts + Tailwind CSS  
**Deployment:** Render (backend) + Vercel (frontend)

## Technical Highlights

- **Data Batching:** Metrics are buffered and flushed once per second, preventing WebSocket flooding.
- **Render Throttling:** `requestAnimationFrame` decouples network frames from React renders, maintaining 60fps under load.
- **Real-Time Streaming:** WebSocket connection via Django Channels with Redis as the channel layer.
- **Professional UI:** Dark/Light theme with state persistence, fully responsive.

## Live Demo

- **Frontend:** https://omnipulse.vercel.app
- **Backend API:** https://omnipulse-backend.onrender.com

## Local Development

### Backend
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

### Frontend

cd frontend
npm install
npm run dev
