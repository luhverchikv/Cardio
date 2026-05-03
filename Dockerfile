# ---- Dockerfile for Cardio Telegram Bot ----
# Use a lightweight Python image
FROM python:3.11-slim

# Install OS‑level dependencies required for audio processing and Vosk
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libopus0 \
        # Vosk requires libsndfile for reading wav files
        libsndfile1 \
        # git is handy for pulling submodules (optional)
        git && \
    rm -rf /var/lib/apt/lists/*

# Create a non‑root user to run the bot
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID appuser && \
    useradd -u $UID -g appuser -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy only the requirements file first (leverages Docker cache)
COPY Cardio_repo/Cardio-main/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY Cardio_repo/Cardio-main/ /app/

# Change ownership of the workdir to the non‑root user
RUN chown -R appuser:appuser /app

# Switch to the non‑root user
USER appuser

# Set environment variables (you can override them at runtime)
ENV PYTHONUNBUFFERED=1

# Expose nothing (Telegram bot uses outbound connections only)
# EXPOSE 80

# Default command – start the bot (adjust if the entry point differs)
CMD ["python", "main.py"]
