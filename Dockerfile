FROM python:3.10-slim

# Install system dependencies (ffmpeg and OpenCV requirements)
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libgl1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy source files
COPY . /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Railway
EXPOSE 8000

# Run the Flask app
CMD ["python", "main.py"]
