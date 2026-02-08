# Orki Voice Agent — Full Integration Document

What's needed to turn the current browser-only voice agent into a full production system integrated with **WhatsApp** and **phone numbers**.

## What the Project Does Today

A browser-based voice agent that onboards MENA businesses through an 8-step conversation to configure their AI customer service agent. Users speak into a web UI, and Gemini (native audio) guides them through setting up agent name, personality, languages, interaction steps, conversation examples, handover triggers, and custom instructions. The output is a structured JSON configuration saved to disk.

**Current flow:** Browser → WebSocket → FastAPI → Google ADK (Gemini) → WebSocket → Browser

## Architecture Overview (Current vs Full)

```
CURRENT:

  Browser (mic) ──WebSocket──> FastAPI ──> Google ADK (Gemini)
                                             │
                                             └──> JSON file output

FULL PRODUCTION:
  Browser (mic) ───WebSocket───┐
  WhatsApp ────Webhook/API─────┤
  Phone Call ──Twilio Stream───┤
                               ▼
                         ┌──────────┐     ┌──────────┐     ┌──────────┐
                         │  Channel │     │  FastAPI  │     │  Google  │
                         │  Router  │────>│  + ADK    │────>│  Gemini  │
                         └──────────┘     └──────────┘     └──────────┘
                               │               │
                         ┌─────┴─────┐   ┌─────┴──────┐
                         │  Message   │   │  Database  │
                         │  Queue     │   │  (Postgres)│
                         └───────────┘   └────────────┘
```

---

## 1. WhatsApp Integration

WhatsApp connects via the **Meta WhatsApp Business Cloud API**. This requires a webhook endpoint to receive messages and an API client to send responses.

### Accounts & Setup Required

| Requirement                   | Where to Get It                                      |
|-------------------------------|------------------------------------------------------|
| Meta Business Account         | https://business.facebook.com                        |
| WhatsApp Business App         | https://developers.facebook.com/apps                 |
| WhatsApp Business Phone Number| Provisioned via Meta Business Manager                |
| Cloud API Access Token        | Meta Developer Dashboard → WhatsApp → API Setup      |
| Webhook Verify Token          | You create this (any random string)                  |
| Public HTTPS URL              | ngrok (dev) or production domain                     |

### New Environment Variables

```bash
# WhatsApp Cloud API

WHATSAPP_ACCESS_TOKEN=your_meta_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
```

### New Files Needed

```
voice_agent/
├── channels/                        # New: multi-channel support
│   ├── __init__.py
│   ├── base.py                      # Abstract channel interface
│   ├── web.py                       # Existing WebSocket channel (refactored)
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   ├── webhook.py               # POST /webhook/whatsapp - receives messages
│   │   ├── client.py                # Sends messages via Cloud API
│   │   ├── audio.py                 # OGG Opus <-> PCM conversion
│   │   └── models.py                # WhatsApp message models
│   └── telephony/
│       ├── __init__.py
│       ├── webhook.py               # Twilio webhook handlers
│       ├── stream.py                # Twilio Media Streams (WebSocket)
│       ├── client.py                # Twilio REST API client
│       └── models.py                # Telephony models
```

### New Endpoints Needed

| Method | Endpoint                    | Description                              |
|--------|-----------------------------|------------------------------------------|
| GET    | `/webhook/whatsapp`         | Meta webhook verification (challenge)    |
| POST   | `/webhook/whatsapp`         | Receive incoming WhatsApp messages       |
| POST   | `/api/whatsapp/send`        | Send outbound WhatsApp message (admin)   |

### WhatsApp Webhook Handler (What It Does)


```
Incoming WhatsApp Message
    │
    ├── Text message ──> Convert to agent text input
    ├── Voice note ────> Download OGG ──> Convert to PCM ──> Agent audio input
    └── Image/Doc ─────> Acknowledge (not supported in v1)
         │
         ▼
    Agent processes via Google ADK
         │
         ├── Text response ──> Send via WhatsApp Cloud API
         └── Audio response ──> Convert PCM to OGG ──> Send as voice note
```

### Audio Format Conversion

WhatsApp uses **OGG Opus** for voice notes. The current system uses **raw PCM**. You need:

| Conversion          | Library        | Direction                        |
|---------------------|----------------|----------------------------------|
| OGG Opus → PCM 16k  | `pydub` + `ffmpeg` | WhatsApp voice note → Agent input |
| PCM 24k → OGG Opus  | `pydub` + `ffmpeg` | Agent output → WhatsApp voice note|

New dependency:
```
pydub>=0.25.1
```

System dependency:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
apt-get install ffmpeg
```

### WhatsApp Session Management

Current sessions are WebSocket-based (live connection). WhatsApp is **stateless HTTP** — each message is a separate request. You need:

- **Session persistence**: Store conversation state in a database (not just in-memory)
- **Session timeout**: Auto-expire sessions after inactivity (e.g., 30 minutes)
- **Session lookup**: Map WhatsApp phone number → active session
- **Conversation continuity**: Load previous state when a user sends a new message

---

## 2. Phone Number / Voice Call Integration

Phone calls connect via **Twilio** (or similar: Vonage, Plivo). Twilio provides real-time audio streaming over WebSocket.

### Accounts & Setup Required

| Requirement           | Where to Get It                          |
|-----------------------|------------------------------------------|
| Twilio Account        | https://www.twilio.com/try-twilio        |
| Twilio Phone Number   | Twilio Console → Phone Numbers → Buy     |
| Account SID           | Twilio Console → Dashboard               |
| Auth Token            | Twilio Console → Dashboard               |
| TwiML App (optional)  | Twilio Console → Voice → TwiML Apps      |

### New Environment Variables

```bash
# Twilio Voice

TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/webhook/twilio/voice
```

### New Endpoints Needed

| Method | Endpoint                         | Description                            |
|--------|----------------------------------|----------------------------------------|
| POST   | `/webhook/twilio/voice`          | Incoming call handler (returns TwiML)  |
| POST   | `/webhook/twilio/status`         | Call status callback                   |
| WS     | `/ws/twilio/stream/{call_sid}`   | Twilio Media Streams WebSocket         |

### Phone Call Flow

```
Incoming Call to Twilio Number
    │
    ▼
Twilio sends POST to /webhook/twilio/voice
    │
    ▼
Server returns TwiML with <Stream> directive
    │
    ▼
Twilio opens WebSocket to /ws/twilio/stream/{call_sid}
    │
    ├── Twilio sends MULAW 8kHz audio chunks
    │       └──> Resample to PCM 16kHz ──> Agent audio input
    │
    └── Agent returns PCM 24kHz audio
            └──> Resample to MULAW 8kHz ──> Stream back to Twilio
```

### Audio Format Conversion (Telephony)

Phone audio is **MULAW 8kHz mono**. The current system uses **PCM 16k/24k**.

| Conversion            | Library          | Direction                    |
|-----------------------|------------------|------------------------------|
| MULAW 8k → PCM 16k   | `audioop` / `pydub` | Phone audio → Agent input  |
| PCM 24k → MULAW 8k   | `audioop` / `pydub` | Agent output → Phone audio |

New dependency:
```
twilio>=9.0.0
```

---

## 3. Database Layer (Required for Both)

The current system saves conversation outputs as JSON files. For multi-channel production use, you need a proper database.

### Why

| Current (File-Based)          | Needed (Database)                              |
|-------------------------------|------------------------------------------------|
| JSON files on disk            | PostgreSQL or MongoDB                          |
| In-memory session state       | Persistent sessions across restarts            |
| No user identity              | Phone number / WhatsApp ID as user identity    |
| Single server only            | Multi-instance ready                           |
| No conversation history       | Full conversation history per user             |

### New Files Needed

```
voice_agent/
├── db/
│   ├── __init__.py
│   ├── engine.py                # Database connection & engine
│   ├── models.py                # SQLAlchemy / ODM models
│   ├── session_store.py         # Session CRUD (replaces in-memory dict)
│   └── conversation_store.py    # Conversation history & state persistence
```

### Schema (Minimum)

```sql
-- Users identified by channel + external ID
CREATE TABLE users (
    id UUID PRIMARY KEY,
    channel VARCHAR(20) NOT NULL,          -- 'web', 'whatsapp', 'phone'
    external_id VARCHAR(100) NOT NULL,     -- phone number or user_id
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(channel, external_id)
);

-- Sessions persist across HTTP requests
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    conversation_state JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Message history
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    direction VARCHAR(10) NOT NULL,        -- 'inbound' or 'outbound'
    content_type VARCHAR(20) NOT NULL,     -- 'text', 'audio', 'tool_call'
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Completed agent configurations
CREATE TABLE agent_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    config JSONB NOT NULL,                 -- The final conversation_state
    created_at TIMESTAMP DEFAULT NOW()
);
```

New dependencies:
```
sqlalchemy>=2.0.0
asyncpg>=0.30.0          # PostgreSQL async driver
alembic>=1.14.0           # Database migrations
```

---

## 4. Channel Router / Adapter Layer

A unified interface so the agent doesn't care which channel the message came from.

### Abstract Channel Interface

```python
# voice_agent/channels/base.py

class ChannelAdapter(ABC):
    """All channels implement this interface."""

    @abstractmethod
    async def receive_message(self, raw_input) -> AgentInput:
        """Convert channel-specific input to unified agent input."""
        pass

    @abstractmethod
    async def send_response(self, session_id: str, response: AgentOutput) -> None:
        """Convert agent output to channel-specific format and send."""
        pass

    @abstractmethod
    async def get_or_create_session(self, external_id: str) -> SessionData:
        """Look up or create session for this user."""
        pass
```

This lets the existing agent logic (`core/agent.py`, `tools/`) work unchanged across all channels.

---

## 5. Message Queue (Recommended for Production)

WhatsApp has strict response time limits (webhook must respond in <15 seconds). A queue decouples message receipt from agent processing.

| Option          | Use Case                     |
|-----------------|------------------------------|
| Redis + Celery  | Simple, well-documented      |
| RabbitMQ        | More robust, better routing  |
| AWS SQS         | If deploying to AWS          |

New dependencies (if using Redis):
```
redis>=5.0.0
celery>=5.4.0
```

---

## 6. Deployment Infrastructure

### Local Development

```bash
# Expose local server to internet (required for WhatsApp/Twilio webhooks)
ngrok http 8006
# Use the ngrok HTTPS URL for webhook configuration
```

### Production

| Component            | Recommended                               |
|----------------------|-------------------------------------------|
| Server               | AWS EC2 / GCP Compute / DigitalOcean      |
| Container            | Docker + docker-compose                   |
| Reverse Proxy        | Nginx or Caddy (handles SSL)              |
| Database             | Managed PostgreSQL (RDS, Cloud SQL, etc.) |
| Domain + SSL         | Real domain with Let's Encrypt            |
| Process Manager      | Gunicorn with Uvicorn workers             |
| Queue (optional)     | Managed Redis (ElastiCache, Memorystore)  |

### Docker Setup Needed

```
├── Dockerfile
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
```

---

## 7. New Dependencies Summary

Add to `requirements.txt`:

```
# WhatsApp
httpx>=0.28.0                              # Already present
pydub>=0.25.1                              # Audio format conversion

# Telephony
twilio>=9.0.0                              # Twilio Voice + Media Streams

# Database
sqlalchemy>=2.0.0                          # ORM
asyncpg>=0.30.0                            # PostgreSQL async driver
alembic>=1.14.0                            # Migrations

# Queue (optional, for production)
redis>=5.0.0
celery>=5.4.0

# Deployment
gunicorn>=23.0.0                           # Production WSGI server
```

System dependencies:
```bash
# Required for audio conversion
ffmpeg

# Required for database
postgresql
```

---

## 8. Updated Environment Variables (Full)

```bash
# ─── Required ───────────────────────────────────────────────
GOOGLE_API_KEY=your_api_key

# ─── WhatsApp Cloud API ────────────────────────────────────
WHATSAPP_ACCESS_TOKEN=your_meta_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id

# ─── Twilio Voice ──────────────────────────────────────────
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# ─── Database ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orki

# ─── Redis (optional) ─────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── Server ────────────────────────────────────────────────
SERVER_HOST=0.0.0.0
SERVER_PORT=8006
BASE_URL=https://your-domain.com

# ─── Phoenix Tracing (optional) ───────────────────────────
PHOENIX_API_KEY=your_phoenix_key
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/your-space
PHOENIX_PROJECT_NAME=voice-agent-tools
ENABLE_PHOENIX_TRACING=true
```

---

## Full Project Structure (After Integration)

```
voice_agent/                              # Main Python package
├── __init__.py
├── __main__.py                           # Entry point
├── main.py                               # FastAPI app factory
├── api/
│   ├── models.py                         # Pydantic request/response models
│   └── routes.py                         # HTTP endpoints (existing + new)
├── business/
│   ├── extractor.py                      # Website scraping & parsing
│   └── models.py                         # Business data models
├── channels/                             # NEW: multi-channel support
│   ├── __init__.py
│   ├── base.py                           # Abstract channel interface
│   ├── web.py                            # Browser WebSocket channel
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   ├── webhook.py                    # WhatsApp webhook handler
│   │   ├── client.py                     # WhatsApp Cloud API client
│   │   ├── audio.py                      # OGG Opus <-> PCM conversion
│   │   └── models.py                     # WhatsApp message models
│   └── telephony/
│       ├── __init__.py
│       ├── webhook.py                    # Twilio voice webhook
│       ├── stream.py                     # Twilio Media Streams handler
│       ├── client.py                     # Twilio API client
│       └── models.py                     # Telephony models
├── config/
│   ├── agent_instructions.py             # Agent prompt templates
│   ├── observability.py                  # Phoenix tracing setup
│   └── settings.py                       # Environment variables (extended)
├── core/
│   ├── agent.py                          # Agent factory (unchanged)
│   ├── session.py                        # Session management (extended)
│   └── state.py                          # Conversation state (unchanged)
├── db/                                   # NEW: database layer
│   ├── __init__.py
│   ├── engine.py                         # Database connection
│   ├── models.py                         # SQLAlchemy models
│   ├── session_store.py                  # Persistent session store
│   └── conversation_store.py             # Conversation history
├── static/
│   ├── business_context.html             # Business input page
│   └── enhanced_ui.html                  # Voice configuration UI
├── tools/                                # Agent tools (unchanged)
│   ├── base.py
│   ├── configuration.py
│   ├── constants.py
│   └── registry.py
└── websocket/                            # WebSocket handling (existing)
    ├── handlers.py
    ├── messaging.py
    └── protocol.py

# Root files
├── Dockerfile                            # NEW: container image
├── docker-compose.yml                    # NEW: full stack orchestration
├── nginx/
│   └── nginx.conf                        # NEW: reverse proxy config
├── alembic/                              # NEW: database migrations
│   ├── alembic.ini
│   └── versions/
├── start.sh                              # Server startup script
├── create_cert.sh                        # SSL certificate generator
├── test_tools.py                         # Tool unit tests
├── test_e2e.py                           # End-to-end browser tests
├── requirements.txt                      # Python dependencies (extended)
├── .env.example                          # Environment template (extended)
└── conversation_outputs/                 # Saved conversation logs
```

---

## Integration Step-by-Step Checklist

### Phase 1: Database & Session Persistence
- [ ] Set up PostgreSQL
- [ ] Create SQLAlchemy models (users, sessions, messages, agent_configs)
- [ ] Set up Alembic migrations
- [ ] Replace in-memory session dict with database-backed session store
- [ ] Replace JSON file output with database persistence
- [ ] Verify existing web flow still works with new session store

### Phase 2: Channel Abstraction
- [ ] Create `channels/base.py` abstract interface
- [ ] Refactor existing WebSocket flow into `channels/web.py`
- [ ] Create channel router in `api/routes.py`
- [ ] Verify existing web flow still works after refactor

### Phase 3: WhatsApp Integration
- [ ] Create Meta Business Account and WhatsApp Business App
- [ ] Provision a WhatsApp Business phone number
- [ ] Implement webhook verification endpoint (GET)
- [ ] Implement message receiver endpoint (POST)
- [ ] Build WhatsApp Cloud API client for sending messages
- [ ] Build OGG Opus ↔ PCM audio converter
- [ ] Implement WhatsApp channel adapter
- [ ] Map phone numbers to sessions in database
- [ ] Handle session timeout and re-engagement
- [ ] Test text message flow end-to-end
- [ ] Test voice note flow end-to-end

### Phase 4: Phone Call Integration
- [ ] Create Twilio account and buy a phone number
- [ ] Implement voice webhook (returns TwiML with `<Stream>`)
- [ ] Implement Twilio Media Streams WebSocket handler
- [ ] Build MULAW 8kHz ↔ PCM 16k/24k audio converter
- [ ] Implement telephony channel adapter
- [ ] Handle call status callbacks (completed, failed, busy)
- [ ] Test inbound call flow end-to-end

### Phase 5: Production Deployment
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml (app + postgres + redis + nginx)
- [ ] Configure Nginx reverse proxy with SSL
- [ ] Set up proper domain and Let's Encrypt certificate
- [ ] Configure webhook URLs in Meta and Twilio dashboards
- [ ] Set up logging and monitoring
- [ ] Load test with concurrent sessions

---

## Troubleshooting (New Issues)

| Issue                    | Solution                                           |
|--------------------------|----------------------------------------------------|
| WhatsApp not receiving   | Check ngrok is running and webhook URL is correct  |
| Twilio call drops        | Verify TwiML `<Stream>` URL matches your server    |
| Audio garbled            | Check ffmpeg is installed for format conversion    |
| Database errors          | Verify `DATABASE_URL` and run `alembic upgrade head` |
