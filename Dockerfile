# ---- Stage 1: Build Frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python Backend + Serve Frontend ----
FROM python:3.12-slim

# HF Spaces requires non-root user with uid 1000
RUN useradd -m -u 1000 user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Switch to non-root user BEFORE installing deps
USER user

# Install Python dependencies as non-root
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy backend code
COPY --chown=user app/ ./app/

# Copy built frontend from stage 1
COPY --from=frontend-build --chown=user /app/frontend/dist ./frontend/dist

# Create uploads directory with user permissions
RUN mkdir -p uploads/avatars uploads/status

# HF Spaces runs on port 7860
EXPOSE 7860

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
