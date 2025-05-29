#!/bin/bash

# Run Streamlit app 
source venv/bin/activate
# Export environment variables from .env files
# 1. deckoviz_ai/.env
if [ -f .env ]; then
  set -a && source .env && set +a
fi
# 2. streamlit/.env
if [ -f streamlit/.env ]; then
  set -a && source streamlit/.env && set +a
fi
streamlit run streamlit/app.py
