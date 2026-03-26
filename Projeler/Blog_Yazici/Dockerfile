FROM python:3.11-slim

# Sistem bağımlılıkları: ffmpeg (frame extraction), libglib2.0 (opencv-headless)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache-busting: requirements değiştiğinde layer yeniden oluşturulur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_pipeline.py", "--from-notion"]
