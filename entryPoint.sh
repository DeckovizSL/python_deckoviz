#!/bin/bash

# Start uvicorn with extended timeouts for AI processing
uvicorn main:app --host 0.0.0.0 --port 8082 --reload --timeout-keep-alive 300 --timeout-graceful-shutdown 30