FROM  python:3.10-slim

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Copy application package
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8082
  
 
 