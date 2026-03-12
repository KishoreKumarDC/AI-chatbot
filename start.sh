#!/usr/bin/env bash

echo "Starting FastAPI..."
uvicorn backend.app:app --host 0.0.0.0 --port $PORT &

echo "Starting Telegram bot..."
python telegram_bot.py
