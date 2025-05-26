FROM python:3.10-slim

# Install system dependencies (ffmpeg and OpenCV requirements)
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libgl1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all source files (make sure static/ and main.py are present)
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir flask opencv-python-headless

# Expose port for Railway (default: 8000)
EXPOSE 8000

# Run the Flask app
CMD ["python", "main.py"]
