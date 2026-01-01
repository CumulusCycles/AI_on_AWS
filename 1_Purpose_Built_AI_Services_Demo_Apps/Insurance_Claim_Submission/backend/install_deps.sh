#!/bin/bash
# Script to ensure dependencies are installed correctly

cd "$(dirname "$0")"

echo "Checking virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
uv pip install -r requirements.txt

echo "Verifying installation..."
python -c "import boto3, fastapi; print('✓ All dependencies installed successfully!')"

echo ""
echo "You can now run: python main.py"

