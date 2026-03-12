---
title: Rchat.ai
emoji: 💬
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
---

# Rchat.ai

A WhatsApp-style real-time chat platform with AI integration and Conversation Autopilot.

## Features
- Real-time messaging with Socket.IO
- AI-powered chat assistant (Groq/Llama)
- Conversation Autopilot — AI handles messages while you're away
- User profiles, statuses, group chats
- End-to-end security hardening

## Environment Variables (set in HF Space Settings → Secrets)

| Variable | Required | Description |
|---|---|---|
| `JWT_SECRET_KEY` | Yes | Random 256-bit secret for JWT signing |
| `DATABASE_URL` | Yes | PostgreSQL connection string (Neon recommended) |
| `GROQ_API_KEY` | Yes | Groq API key for AI features |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (defaults to same-origin) |
| `COOKIE_SECURE` | No | Set `true` for HTTPS deployments |
| `ENV` | No | Set `production` for production mode |

## Local Development

```bash
# Backend
cd Rchat.ai-
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your values
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install && npm run dev
```
