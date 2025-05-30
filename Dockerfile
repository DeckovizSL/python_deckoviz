FROM python:3.12-slim-bullseye

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Copy application package
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8082
  
 
 