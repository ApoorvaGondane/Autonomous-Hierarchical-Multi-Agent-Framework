# Use a lightweight Python 3.10 base image
FROM python:3.11-slim

# Set working directory and prevent Python from writing .pyc files
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_DISABLE_PROGRESS_BARS=1
ENV CREWAI_DEBUG=true
ENV LITELLM_LOG=DEBUG
# Install system dependencies required for building specific Python packages
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn streamlit streamlit-mermaid

# Copy the application source code
COPY src/ /app/src/
COPY chroma_db/ /app/chroma_db/

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501