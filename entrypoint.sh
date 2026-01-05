#!/bin/bash
set -e

echo "⏳ Waiting for MinIO to be ready..."
sleep 5

echo "📦 Uploading NDA templates to MinIO..."
python scripts/upload_templates.py

echo "🚀 Starting NDA Backend API..."
exec python run.py
