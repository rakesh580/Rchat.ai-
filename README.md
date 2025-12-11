# 🧠 AI-Powered Real-Time Chat Platform

A real-time, AI-augmented chat platform built with **FastAPI**, **React + Vite**, **WebSockets**, and **PostgreSQL**, featuring intelligent modules like moderation, smart replies, and sentiment analysis.

Future expansion includes **polyglot persistence** with **MongoDB** for messages and **PostgreSQL** for user data.

---

## 🚀 Features

- 🔁 Real-time chat with WebSocket support (room-based)
- 🤖 AI features: Smart Replies, Sentiment Detection, Toxicity Moderation
- 🧠 LLM Integration via OpenAI or Ollama APIs
- 🗂️ Scalable PostgreSQL-backed user and session management
- 🌍 Planned MongoDB integration for flexible message storage
- 🧩 Modular FastAPI backend with JWT Auth and API versioning
- 🎨 React + Vite frontend with interactive UI and dark mode
- 📈 Message analytics and moderation insights (optional)

---

## 🧰 Tech Stack

**Frontend**
- React + Vite
- TailwindCSS
- WebSockets

**Backend**
- FastAPI (Python 3.10+)
- PostgreSQL (via SQLAlchemy or asyncpg)
- WebSockets (`fastapi.WebSocket`)
- JWT Auth (via `pyjwt`)
- LangChain / OpenAI / Llama-index (AI features)
- MongoDB (planned polyglot message storage)

**DevOps**
- Docker + Docker Compose
- GitHub Actions (CI/CD)
- Nginx (optional)
- GitHub Pages (for static preview)

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/rakesh580/ai-chat-platform.git
cd ai-chat-platform

# Backend Setup
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend Setup
cd ../frontend
npm install
npm run dev
