# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the local requirements.txt to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]
