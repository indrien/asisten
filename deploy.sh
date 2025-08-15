#!/bin/bash

# Deployment script untuk Bot Telegram Asisten

echo "🚀 Starting deployment process..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running the bot."
    echo "   Required variables: BOT_TOKEN, API_ID, API_HASH, GEMINI_API_KEY, OWNER_ID"
    read -p "Press Enter after editing .env file..."
fi

# Validate environment
echo "✅ Validating environment..."
python3 -c "
from config.settings import settings
try:
    settings.validate()
    print('✅ Environment validation passed!')
except Exception as e:
    print(f'❌ Environment validation failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Environment validation failed. Please check your .env file."
    exit 1
fi

# Check MongoDB connection
echo "🔗 Testing database connection..."
python3 -c "
import asyncio
from config.database import test_connection
asyncio.run(test_connection())
"

if [ $? -ne 0 ]; then
    echo "⚠️ Database connection test failed. Bot will still start but database features may not work."
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "To start the bot:"
echo "  source venv/bin/activate"
echo "  python3 main.py"
echo ""
echo "To run as service (optional):"
echo "  sudo cp telegram-bot.service /etc/systemd/system/"
echo "  sudo systemctl enable telegram-bot"
echo "  sudo systemctl start telegram-bot"
