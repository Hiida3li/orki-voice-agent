#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Voice Agent with Tools - Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Phoenix configuration
echo "📊 Checking Phoenix observability..."
python -c "from phoenix_config import get_phoenix_info; info = get_phoenix_info(); print(f'   Status: {info[\"status\"]}'); print(f'   Enabled: {info[\"enabled\"]}'); print(f'   Configured: {info[\"configured\"]}')"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Please create a .env file with your GOOGLE_API_KEY"
    exit 1
fi

# Check if Google API key is set
if ! grep -q "GOOGLE_API_KEY" .env; then
    echo -e "${YELLOW}⚠️  GOOGLE_API_KEY not found in .env${NC}"
    echo "Please add GOOGLE_API_KEY to your .env file"
    exit 1
fi

# Install dependencies
echo ""
echo "Checking dependencies..."
pip install -q google-adk fastapi uvicorn python-dotenv websockets

# Run tests
echo ""
echo -e "${BLUE}Running tool tests...${NC}"
python test_tools.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Starting server...${NC}"
    echo ""
    echo "🌐 Server will be available at:"
    echo "   http://localhost:8006/pcm"
    echo ""
    echo "📁 JSON files will be saved to:"
    echo "   ./conversation_outputs/"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""

    # Start the server
    python live_streaming_server.py
else
    echo ""
    echo -e "${YELLOW}⚠️  Tests failed. Please fix errors before starting server.${NC}"
    exit 1
fi
