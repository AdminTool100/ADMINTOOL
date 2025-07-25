#!/bin/bash
# Khởi động FastAPI server
echo "🚀 Starting FastAPI server on port 10000..."
uvicorn main:app --host 0.0.0.0 --port 10000