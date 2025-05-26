FROM python:3.10-slim

# Install ffmpeg and OpenCV dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files to container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port Railway expects
EXPOSE 8080

# Run the app using Gunicorn with dynamic port binding
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:${PORT:-8080} --timeout 120"]
