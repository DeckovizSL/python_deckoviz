FROM python:3.12-slim-bullseye

WORKDIR /app

# Install dependencies
COPY deckoviz_ai/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy application package
COPY deckoviz_ai ./deckoviz_ai
ENV PYTHONPATH=/app

# Expose the Streamlit port
EXPOSE 8501

# Create non-root user
RUN useradd -m -d /home/appuser -s /bin/bash appuser

# Create output directory and grant ownership
RUN mkdir -p /app/output && chown appuser:appuser /app/output
USER appuser

# Launch Streamlit app
CMD ["streamlit", "run", "deckoviz_ai/streamlit/app.py", "--server.address=0.0.0.0"]
