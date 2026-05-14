# Orki Voice Agent

Real-time voice interface for configuring AI customer service voice agents.

## Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env and add your own GOOGLE_API_KEY

# 3. Generate SSL certificates
./create_cert.sh

# 4. Run
./start.sh
# Or: python -m voice_agent
# Server starts at https://localhost:8006
```

## Endpoints

| URL             | Description                         |
|-----------------|-------------------------------------|
| `/`             | Redirects to `/business`            |
| `/business`     | Business context input (start here) |
| `/enhanced`     | Voice configuration UI              |
| `/ws/{user_id}` | WebSocket connection                |
| `/health`       | Health check                        |

## Project Structure

```
voice_agent/                  # Main Python package
├── __init__.py
├── __main__.py               # Entry point for python -m voice_agent
├── main.py                   # FastAPI app factory
├── api/                      # HTTP API layer
│   ├── models.py             # Pydantic request/response models
│   └── routes.py             # API endpoints
├── business/                 # Business context extraction
│   ├── extractor.py          # Website scraping & parsing
│   └── models.py             # Business data models
├── config/                   # Configuration
│   ├── agent_instructions.py # Agent prompt templates
│   ├── observability.py      # Phoenix tracing setup
│   └── settings.py           # Environment variables
├── core/                     # Core agent logic
│   ├── agent.py              # Agent factory
│   ├── session.py            # Session management
│   └── state.py              # Conversation state
├── static/                   # Frontend files
│   ├── business_context.html # Business input page
│   └── enhanced_ui.html      # Voice configuration UI
├── tools/                    # Agent tools
│   ├── base.py               # Base validators & helpers
│   ├── configuration.py      # Configuration tool implementations
│   ├── constants.py          # Valid options & limits
│   └── registry.py           # Tool registration
└── websocket/                # WebSocket handling
    ├── handlers.py           # Connection lifecycle
    ├── messaging.py          # Bidirectional message routing
    └── protocol.py           # Message types & encoding

# Root files
├── start.sh                  # Server startup script
├── create_cert.sh            # SSL certificate generator
├── test_tools.py             # Tool unit tests
├── test_e2e.py               # End-to-end browser tests
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── conversation_outputs/     # Saved conversation logs (clean it up)
```

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_api_key          # From https://aistudio.google.com/apikey

# Optional (Phoenix tracing)
PHOENIX_API_KEY=your_phoenix_key
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/your-space
PHOENIX_PROJECT_NAME=voice-agent-tools
ENABLE_PHOENIX_TRACING=true
```

## Configuration Tools

The agent uses these tools to capture structured configuration:

| Tool                                    | Purpose                             |
|-----------------------------------------|-------------------------------------|
| `get_agent_name(name)`                  | Set agent name                      |
| `get_agent_gender(gender)`              | Male or Female                      |
| `get_personality(personality)`          | Communication style                 |
| `get_languages(languages[])`            | Supported languages                 |
| `get_dialect(dialect)`                  | Arabic dialect (if Arabic selected) |
| `get_interaction_steps(steps[])`        | Conversation workflow (2-5 steps)   |
| `get_conversation_examples(examples[])` | Brand voice examples                |
| `get_handover_reasons(reasons[])`       | Human escalation triggers           |
| `get_additional_instructions(text)`     | Custom behavioral rules             |
| `conversation_complete(reason)`         | Signal completion                   |

### Valid Options

**Personalities:** Empathetic and Friendly, Formal and Professional, Salesperson, Fun and Humorous, Casual and Down-To-Earth

**Languages:** English, Arabic, Hindi, Urdu

**Arabic Dialects:** Omani, Saudi, Bahraini, Kuwaiti, Qatari, Emirati, Fusha (MSA)

## Technical Details

### Audio Settings
- Input: 16kHz mono PCM
- Output: 24kHz mono PCM
- Model: `gemini-2.5-flash-native-audio-latest` # After testing different models this one is the fastest
- Voice: Charon

### WebSocket Protocol

**Client to Server (audio):**
```
{"mime_type": "audio/pcm", "data": "base64_encoded_audio"}
```

**Server to Client (responses):**
```
{"mime_type": "audio/pcm", "data": "base64_audio"}
{"mime_type": "text/plain", "data": "transcription"}
{"type": "tool_call", "tool_name": "...", "arguments": {...}}
{"type": "tool_result", "tool_name": "...", "result": {...}}
{"type": "state_update", "conversation_state": {...}}
{"turn_complete": true}
```

**Interruption:**
```
// Client sends when user speaks during AI response
{"type": "user_speaking"}
// Server confirms
{"interrupted": true}
```

## Testing

```bash
# Run tool unit tests
python test_tools.py

# Run end-to-end tests (requires Playwright)
pip install playwright
playwright install chromium
python test_e2e.py
```

## Troubleshooting

| Issue               | Solution                                           |
|---------------------|----------------------------------------------------|
| Microphone error    | Allow microphone in browser settings               |
| Connection error    | Ensure server is running, use `https://`           |
| Certificate warning | Click "Advanced" -> "Proceed" (safe for local dev) |
| No audio output     | Check browser volume and system audio              |
| Tools not working   | Verify `GOOGLE_API_KEY` in `.env`                  |

## Key Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `google-adk` - Google Agent Development Kit
- `google-genai` - Gemini API client
- `websockets` - WebSocket support
- `httpx` / `beautifulsoup4` - Business context extraction
- `arize-phoenix-otel` - Observability (optional)

See `requirements.txt` for the complete list.
