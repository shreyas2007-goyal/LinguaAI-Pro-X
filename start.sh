#!/usr/bin/env bash
# LinguaAI Pro X — one command to set up and run. No Node.js needed.
set -e

if [ ! -d "venv" ]; then
  echo "Setting up (first time only, takes a minute)..."
  python3 -m venv venv
  ./venv/bin/pip install --quiet --upgrade pip
  ./venv/bin/pip install --quiet -r requirements.txt
fi

echo "Starting LinguaAI Pro X — your browser will open automatically..."
./venv/bin/streamlit run app.py
