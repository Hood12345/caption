FROM python:3.10-slim

# Install ffmpeg and OpenCV dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libgl1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install flask opencv-python-headless

# Expose port
EXPOSE 8000

CMD ["python", "main.py"]
