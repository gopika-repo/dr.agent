# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# git is required by gitpython to clone repositories
RUN apt-get update && apt-get install -y --no-install-recommends     git     build-essential     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the API port
EXPOSE 8000

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Run the FastAPI server by default
# We use uvicorn to run the app in api.py
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
