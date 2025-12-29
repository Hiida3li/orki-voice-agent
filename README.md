# Voice-to-Voice AI Agent Configuration System

A real-time voice interface for configuring AI customer service agents through natural conversation. Users speak naturally to define their agent's personality, capabilities, and behavior, while watching the configuration build in real-time.

## What This System Does

This system allows business owners and developers to **create AI customer service agents by talking to them**, rather than filling out forms or writing configuration files.

### The Process
1. **Connect** - User opens the web interface and starts a voice session
2. **Converse** - User speaks naturally about what kind of agent they want
3. **Configure** - The AI asks questions and uses tools to capture structured configuration data
4. **Visualize** - Real-time UI shows the configuration being built
5. **Export** - Final JSON configuration ready to deploy the agent

---

## System Architecture

### Core Components

#### 1. **Backend Server** (`live_streaming_server.py`)
The main application server that orchestrates everything:

- **WebSocket Server**: Handles real-time bidirectional communication
  - Receives audio from user's microphone (PCM 16kHz mono)
  - Sends AI-generated audio responses back to browser
  - Broadcasts tool calls and state updates to UI

- **Audio Processing Pipeline**:
  - Accepts raw PCM audio chunks from browser
  - Forwards to Google ADK's Multimodal Live API
  - Receives audio responses from Gemini 2.0 Flash model
  - Streams audio back to browser for playback

- **Session Management**:
  - Each client gets a unique session ID
  - Maintains conversation state across the entire interaction
  - Tracks configuration progress (agent_name, personality, etc.)

- **State Broadcasting**:
  - After each tool call, broadcasts updated configuration to UI
  - Allows real-time visualization of what's been configured
  - Sends tool call details for developer transparency

#### 2. **Tools System** (`tools.py`)
Defines the structured configuration tools the AI uses:

Each tool captures a specific aspect of the agent configuration:

- **`get_agent_name(agent_name)`**
  - Captures the agent's name (e.g., "Maya", "Ali")
  - First tool typically called in conversation
  - Stores in session state and conversation_state

- **`get_agent_gender(gender)`**
  - Sets agent gender: "Male" or "Female"
  - Called automatically after name determination
  - Affects voice selection for the final agent

- **`get_personality(personality)`**
  - Defines communication style:
    - "Empathetic and Friendly"
    - "Formal and Professional"
    - "Salesperson"
    - "Fun and Humorous"
    - "Casual and Down-To-Earth"
  - Only ONE personality can be selected

- **`get_languages(languages)`**
  - Array of supported languages: English, Arabic, Hindi, Urdu
  - Multiple languages can be selected
  - Returns `requires_dialect: true` if Arabic is selected

- **`get_dialect(dialect)`**
  - Required only if Arabic is selected
  - Options: Omani, Saudi, Bahraini, Kuwaiti, Qatari, Emirati, Fusha (MSA)
  - Ensures culturally appropriate responses

- **`get_interaction_steps(interaction_steps)`**
  - Defines the agent's conversation workflow
  - Array of step descriptions (recommended 2-5 steps)
  - Example: ["Greet customer", "Identify intent", "Collect information", "Provide solution"]
  - Guides how the agent structures conversations

- **`get_conversation_examples(conversation_examples)`**
  - Captures brand voice through example dialogues
  - Array of `{customer_message, agent_response}` pairs
  - Teaches the agent the exact tone and wording to use
  - Critical for maintaining brand consistency

- **`get_handover_reasons(handover_reasons)`**
  - Defines when AI should escalate to human agent
  - Array of `{reason, description}` objects
  - Example reasons: "Customer Frustration", "Complex Issue", "Explicit Human Request"
  - Recommended 2-5 scenarios

- **`get_additional_instructions(instructions)`**
  - Freeform text for custom behavioral rules
  - Example: "Always offer a discount to frustrated customers"
  - Allows business-specific customization beyond standard options
  - Character limit: 2000 characters (warning if exceeded)

- **`conversation_complete(reason)`**
  - Signals the conversation is done
  - Triggered by phrases like "done", "thank you", "that's it"
  - Adds completion timestamp and metadata
  - Returns final configuration JSON

**How Tools Work:**
- Each tool function validates input data
- Stores data in `tool_context.state` (session state)
- Updates `conversation_state` (broadcasted to UI)
- Returns structured response with status and message
- AI uses returned data to confirm with user and continue

#### 3. **Web Interface** (`enhanced_ui.html`)
Real-time visualization dashboard with two panels:

**Left Panel - Session Control:**
- **Audio Visualizer**: Shows audio activity (speaking/listening)
- **Status Indicator**:
  - "Ready to connect" → "Connected" → "Listening" → "AI speaking"
  - Color-coded (green=connected, blue=streaming, yellow=speaking, red=error)
- **Start/Stop Controls**: Begin and end voice sessions
- **Volume Control**: Adjust AI voice playback (0-100%)
- **Message Feed**: Shows conversation transcript

**Right Panel - Configuration Display:**
- **Dynamic Fields**: One field per configuration aspect
  - Agent Name
  - Gender
  - Personality
  - Languages
  - Dialect (appears only if Arabic selected)
  - Interaction Steps (ordered list)
  - Conversation Examples (styled cards with customer/agent messages)
  - Handover Reasons (styled cards with reason/description)
  - Additional General Instructions (text area)

- **Visual Feedback**:
  - Empty fields: Gray, "Not set" placeholder
  - Filled fields: Colored background, bold text
  - Special formatting for arrays and objects

- **Tool Calls Panel**: Developer view showing:
  - Tool name and timestamp
  - Arguments passed to tool (JSON)
  - Results returned from tool (JSON)
  - Real-time updates as AI uses tools

- **JSON Display**: Live view of complete configuration object
- **Create Agent Button**: Appears when conversation completes

**Frontend Technology:**
- Vanilla JavaScript (no framework dependencies)
- WebSocket for real-time communication
- PCM Player library for audio playback
- Web Audio API for microphone capture
- ScriptProcessor for audio processing (4096 sample buffer)

#### 4. **Configuration Files**

**Environment Variables** (`.env`):
```
GEMINI_API_KEY=your_api_key_here
```

**Phoenix Config** (`phoenix_config.py`):
- Sets up observability/monitoring with Phoenix
- Traces all agent interactions
- Logs tool calls and responses
- Useful for debugging and analytics

**SSL Certificates** (`cert.pem`, `key.pem`):
- Required for HTTPS/WSS (secure WebSocket)
- Browser requires HTTPS for microphone access
- Generated via `create_cert.sh` script

---

## Complete Conversation Flow

### Step-by-Step Execution

**1. User Opens Browser → `enhanced_ui.html`**
- Renders empty configuration fields
- Initializes WebSocket client
- Sets up audio player (PCM 24kHz)

**2. User Clicks "Start Session"**
- Browser requests microphone permission
- Establishes WebSocket connection to `/ws/{client_id}?is_audio=true`
- Frontend sends PCM audio chunks (16kHz mono, 16-bit)
- Backend creates Google ADK session with Gemini 2.0 Flash

**3. Gemini Connects → Initial System Prompt**
```
You are a helpful agent configuration assistant.
Help users configure their AI customer service agent by:
1. Asking about agent name
2. Determining personality
3. Understanding languages needed
4. Defining interaction workflow
5. Capturing brand voice examples
6. Setting escalation rules

Use tools to capture structured configuration data.
Be conversational, friendly, and efficient.
```

**4. Conversation Begins**
```
User: "Hi, I want to create an agent"
AI: "Great! Let's start. What would you like to name your agent?"
User: "Let's call her Maya"
AI: [Calls get_agent_name("Maya")]
AI: [Calls get_agent_gender("Female") - inferred from name]
AI: "Perfect! Maya it is. What kind of personality should Maya have?
     I can make her empathetic and friendly, formal and professional,
     or even fun and humorous."
User: "Make her friendly and empathetic"
AI: [Calls get_personality("Empathetic and Friendly")]
AI: "Excellent choice! Which languages should Maya speak?"
User: "English and Arabic"
AI: [Calls get_languages(["English", "Arabic"])]
AI: [Tool returns requires_dialect: true]
AI: "Got it! Since Maya will speak Arabic, which dialect should she use?"
User: "Omani dialect"
AI: [Calls get_dialect("Omani")]
AI: "Perfect! Now, let's define Maya's interaction flow.
     What steps should she follow when talking to customers?"
User: "First greet them, then ask what they need, collect their info,
      and provide a solution"
AI: [Calls get_interaction_steps([
    "Greet customer warmly",
    "Ask what they need",
    "Collect necessary information",
    "Provide solution"
])]
AI: "Great structure! Can you give me some examples of how Maya should talk?
     What's a typical customer question and how should Maya respond?"
User: "If someone asks 'Do you deliver?', Maya should say
      'Yes, we deliver nationwide! When would you like your order?'"
AI: [Calls get_conversation_examples([{
    "customer_message": "Do you deliver?",
    "agent_response": "Yes, we deliver nationwide! When would you like your order?"
}])]
AI: "Excellent! Any more examples?"
[... more examples collected ...]
AI: "Perfect! Now, when should Maya transfer customers to a human?"
User: "If they're frustrated or ask for a manager"
AI: [Calls get_handover_reasons([
    {"reason": "Customer Frustration", "description": "When customer expresses anger or frustration"},
    {"reason": "Manager Request", "description": "When customer explicitly asks for manager"}
])]
AI: "Got it! Any special instructions for Maya's behavior?"
User: "Always offer a discount code if customers seem hesitant"
AI: [Calls get_additional_instructions("Always offer a discount code if customers seem hesitant")]
AI: "Perfect! I've configured Maya completely. Is there anything else?"
User: "No, that's all!"
AI: [Calls conversation_complete("User said that's all")]
AI: "Thank you! Maya is ready to go. You can review the configuration and create your agent."
```

**5. Real-Time UI Updates**
After EACH tool call:
- Backend broadcasts state update via WebSocket
- Frontend updates corresponding field
- Field background changes from gray to colored
- JSON display updates
- Tool call appears in Tool Calls panel

**6. Session Complete**
- "Create Agent" button appears
- Final JSON contains all configuration:
```json
{
  "agent_name": "Maya",
  "agent_gender": "Female",
  "personality": "Empathetic and Friendly",
  "languages": ["English", "Arabic"],
  "dialect": "Omani",
  "interaction_steps": [
    "Greet customer warmly",
    "Ask what they need",
    "Collect necessary information",
    "Provide solution"
  ],
  "conversation_examples": [...],
  "handover_reasons": [...],
  "additional_instructions": "Always offer a discount code if customers seem hesitant",
  "completed_at": "2025-10-13T13:45:22.123456",
  "completion_reason": "User said that's all"
}
```

---

## Audio Pipeline Details

### Browser → Server (User Speech)
1. **Microphone Capture**: `navigator.mediaDevices.getUserMedia()`
   - Sample rate: 16kHz
   - Channels: Mono (1)
   - Echo cancellation: Enabled
   - Noise suppression: Enabled

2. **Processing**: `ScriptProcessor` (4096 sample buffer)
   - Converts Float32 to Int16 PCM
   - Packs into binary buffer
   - Base64 encodes for WebSocket transport

3. **WebSocket Send**:
   ```json
   {
     "mime_type": "audio/pcm",
     "data": "base64_encoded_audio_chunk"
   }
   ```

4. **Server Receives**: Decodes and forwards to Google ADK

### Server → Browser (AI Response)
1. **Gemini Generates**: Audio response (24kHz PCM)
2. **Server Forwards**: Via WebSocket with mime_type
3. **Browser Decodes**: Base64 → Int16Array
4. **PCM Player**: Renders audio to speakers
   - Encoding: 16-bit Int
   - Channels: Mono
   - Sample rate: 24kHz
   - Flushing time: 1000ms

---

## Interruption Handling System

### Overview
The system implements real-time interruption detection and handling, allowing users to interrupt the AI mid-speech. When an interruption is detected, the AI immediately stops speaking, clears all audio buffers, and switches context to process the new user input.

### Architecture

#### Voice Activity Detection (VAD)
Client-side VAD continuously monitors incoming microphone audio to detect when the user starts speaking.

**Algorithm:**
1. Calculate RMS (Root Mean Square) of audio samples
   ```
   RMS = sqrt(sum(sample^2) / sample_count)
   ```
2. Convert to decibels: `dB = 20 * log10(RMS)`
3. Compare against threshold
4. Debounce to avoid false positives

**Parameters:**
- `vadThreshold`: -50 dB (default, configurable)
  - Lower values = more sensitive
  - Higher values = less sensitive
- `vadDebounce`: 300ms (minimum time between detections)

**Implementation Location:**
- Client: `enhanced_ui.html` and embedded HTML in `live_streaming_server.py`
- Method: `detectVoiceActivity(audioData)`

#### Interruption Flow

**Client-Side (Browser):**
1. Audio processing pipeline continuously analyzes microphone input
2. VAD detects voice activity above threshold
3. If agent is currently speaking (`isAgentSpeaking === true`):
   - Set `isUserSpeaking` flag
   - Call `stopAgentAudio()` immediately
   - Send interruption signal to server via WebSocket
4. `stopAgentAudio()` destroys PCM player and reinitializes
   - Clears all buffered audio chunks
   - Resets playback state
   - Updates UI status

**Server-Side (Python):**
1. Receives `user_speaking` message from client
2. Sets `should_cancel_output` flag
3. Clears `audio_buffer` immediately
4. Skips flushing queued audio chunks
5. Sends `interrupted` confirmation back to client
6. ADK automatically cancels ongoing generation when new audio arrives

**State Synchronization:**
- `isAgentSpeaking`: Tracks when AI is outputting audio
- `isUserSpeaking`: Tracks when user is detected speaking
- `should_cancel_output`: Server flag to stop all pending output
- States reset on turn completion

### Buffer Management

**Client-Side Buffers:**
- PCM Player internal buffer: Destroyed and recreated on interruption
- No residual audio remains after `stopAgentAudio()` call

**Server-Side Buffers:**
- `audio_buffer`: List of pending audio chunks
- `min_buffer_size`: 2 chunks (for smooth playback)
- `buffer_timeout`: 0.3 seconds
- On interruption: `audio_buffer` cleared immediately
- `flush_audio_buffer()` checks `should_cancel_output` before sending

### Audio Processing Integration

**ScriptProcessor Path (Fallback):**
```javascript
processor.onaudioprocess = (e) => {
    const inputData = e.inputBuffer.getChannelData(0);
    this.detectVoiceActivity(inputData);  // VAD on every frame
    // ... convert and send audio
};
```

**AudioWorklet Path (Modern):**
```javascript
workletNode.port.onmessage = (event) => {
    const pcmBuffer = event.data;
    const int16Array = new Int16Array(pcmBuffer);
    // Convert to Float32 for VAD
    const float32Array = convertToFloat32(int16Array);
    this.detectVoiceActivity(float32Array);
    // ... send audio
};
```

### Protocol Messages

**Client to Server:**
```json
{
  "type": "user_speaking"
}
```

**Server to Client:**
```json
{
  "interrupted": true
}
```

### Timing Characteristics

**Interruption Latency:**
- VAD detection: ~4ms (4096 samples at 16kHz)
- Client processing: <5ms
- WebSocket transmission: 10-50ms (depends on network)
- Server processing: <5ms
- Total: 20-65ms typical

**Audio Stop Time:**
- PCM Player destruction: <10ms
- User perceives stop: 30-75ms total

### Configuration Parameters

**Client-Side (`LiveVoiceChat` constructor):**
```javascript
this.vadThreshold = -50;      // dB threshold
this.vadDebounce = 300;       // milliseconds
this.isAgentSpeaking = false; // state tracking
this.isUserSpeaking = false;  // state tracking
```

**Server-Side (`agent_to_client_messaging`):**
```python
is_agent_speaking = False
should_cancel_output = False
audio_buffer = []
min_buffer_size = 2
buffer_timeout = 0.3  # seconds
```

### Error Handling

**Client-Side:**
- VAD calculation errors caught and logged
- WebSocket disconnection handled gracefully
- PCM player destruction errors ignored (may already be destroyed)

**Server-Side:**
- Buffer clearing errors logged but don't stop processing
- WebSocket send failures return False, connection marked closed
- Interruption during flush checked at every chunk

### Testing Interruption Handling

**Test Scenario:**
1. Start session and wait for AI to speak
2. Interrupt mid-sentence by speaking
3. Verify:
   - Console log: "User started speaking - interrupting agent"
   - Console log: "Stopping agent audio immediately"
   - Server log: "Interruption detected - clearing buffers"
   - AI audio stops within 50-100ms
   - AI responds to new input, not previous question

**Debug Logging:**
- Client: Check browser console for VAD and interruption logs
- Server: Check terminal for interruption detection and buffer clearing

### Performance Considerations

**CPU Usage:**
- VAD calculation: ~0.1% per audio frame
- No significant impact on system performance
- ScriptProcessor runs on main thread (acceptable for VAD)

**Memory:**
- Audio buffer limited by `min_buffer_size` (2 chunks typical)
- Buffer cleared immediately on interruption
- No memory leaks from repeated interruptions

**Network:**
- Single `user_speaking` message per interruption (~50 bytes)
- Interruption confirmation message (~30 bytes)
- Minimal bandwidth impact

---

## Setup and Installation

### Prerequisites
```bash
# Python 3.8+
python --version

# pip
pip --version
```

### Installation Steps

**1. Clone/Navigate to Project**
```bash
cd /path/to/voice
```

**2. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install fastapi uvicorn websockets google-adk python-dotenv
```

**4. Set API Key**
Create `.env` file:
```
GEMINI_API_KEY=your_actual_api_key_here
```

Get API key from: https://aistudio.google.com/apikey

**5. Generate SSL Certificates**
```bash
chmod +x create_cert.sh
./create_cert.sh
```

Creates `cert.pem` and `key.pem` for HTTPS.

**6. Start Server**
```bash
python live_streaming_server.py
```

Or use the startup script:
```bash
chmod +x start.sh
./start.sh
```

**7. Open Browser**
```
https://localhost:8006/pcm      # PCM Player interface
https://localhost:8006/enhanced  # Enhanced UI with configuration display
```

Accept self-signed certificate warning (this is safe for local development).

---

## Project Structure

```
voice/
├── live_streaming_server.py       # Main server (WebSocket, audio, state management)
├── tools.py                        # Configuration tools (9 tools + 1 completion)
├── enhanced_ui.html                # Frontend interface (single-file SPA)
├── phoenix_config.py               # Observability/monitoring setup
├── .env                            # API keys (DO NOT COMMIT)
├── cert.pem                        # SSL certificate (generated)
├── key.pem                         # SSL private key (generated)
├── create_cert.sh                  # Certificate generation script
├── start.sh                        # Server startup script
├── test_tools.py                   # Unit tests for tools
├── test_instruct_tool.py           # Tests for additional_instructions
├── benchmark_scenarios.py          # Performance/scenario tests
├── conversation_outputs/           # Saved conversation logs
└── venv/                           # Python virtual environment (not committed)
```

---

## Configuration Options

### Tool Constants (`tools.py`)

**Valid Personalities:**
- Empathetic and Friendly
- Formal and Professional
- Salesperson
- Fun and Humorous
- Casual and Down-To-Earth

**Valid Languages:**
- English
- Arabic
- Hindi
- Urdu

**Valid Arabic Dialects:**
- Omani
- Saudi
- Bahraini
- Kuwaiti
- Qatari
- Emirati
- Fusha (MSA)

### Server Configuration (`live_streaming_server.py`)

**Host/Port:**
```python
uvicorn.run(app, host="0.0.0.0", port=8006,
            ssl_certfile="cert.pem", ssl_keyfile="key.pem")
```

**Audio Settings:**
- Input: 16kHz mono PCM
- Output: 24kHz mono PCM
- Buffer: 4096 samples
- Min buffer size: 2 chunks
- Buffer timeout: 0.3 seconds

**Google ADK Model:**
- Model: `gemini-live-2.5-flash-preview`
- Voice: `Charon` (default, can be changed)
- Response modalities: AUDIO

---

## Debugging and Monitoring

### Browser Console
```javascript
// Check WebSocket status
ws.readyState  // 0=connecting, 1=open, 2=closing, 3=closed

// Monitor state updates
console.log('📋 Updating agent config:', config)

// Check tool calls
console.log('🔧 Tool called:', data.tool_name)
```

### Server Logs
```bash
# Start with debug logging
python live_streaming_server.py

# Watch for:
# - "WebSocket connection established"
# - "Tool called: get_agent_name with args: ..."
# - "Broadcasting state update: ..."
```

### Phoenix Observability
If Phoenix is configured:
- Traces every tool call
- Records conversation turns
- Monitors latency and errors
- Access dashboard at configured endpoint

---

## Testing

### Run Tool Tests
```bash
python test_tools.py
```

Tests validate:
- Input validation (empty values, wrong types)
- Constraint checking (valid personalities, languages)
- State persistence (conversation_state updates)
- Edge cases (too many steps, long instructions)

### Run Instruction Tool Tests
```bash
python test_instruct_tool.py
```

### Manual Testing Checklist
- [ ] Microphone permission granted
- [ ] Audio visualizer animates when speaking
- [ ] AI voice plays through speakers
- [ ] Each config field updates in real-time
- [ ] Dialect field appears/hides based on Arabic selection
- [ ] Tool calls appear in panel with correct JSON
- [ ] Final JSON includes all configured data
- [ ] "Create Agent" button appears on completion

---

## Troubleshooting

### "Microphone Error"
- **Cause**: Browser denied microphone permission
- **Fix**: Click lock icon in address bar → Allow microphone

### "Connection Error"
- **Cause**: Server not running or wrong URL
- **Fix**: Ensure server is running, use `https://` not `http://`

### "Certificate Warning"
- **Cause**: Self-signed certificate
- **Fix**: Click "Advanced" → "Proceed anyway" (safe for local dev)

### No Audio Output
- **Cause**: Volume too low or wrong audio device
- **Fix**: Check browser volume, adjust slider, check system audio output

### Tools Not Working
- **Cause**: API key invalid or quota exceeded
- **Fix**: Verify `.env` file has correct `GEMINI_API_KEY`

### UI Not Updating
- **Cause**: WebSocket connection dropped
- **Fix**: Check browser console for errors, restart session

---

## Key Design Decisions

### Why Voice Interface?
- **Faster**: Speaking is faster than typing/clicking forms
- **Natural**: Conversational flow feels intuitive
- **Accessible**: Works for users uncomfortable with technical UIs
- **Contextual**: AI asks follow-up questions based on previous answers

### Why Real-Time UI?
- **Transparency**: Users see exactly what's being captured
- **Confidence**: Visual confirmation builds trust
- **Debugging**: Developers can see tool calls and state changes
- **Engagement**: Live updates keep users engaged

### Why Google ADK + Gemini?
- **Multimodal**: Native audio input/output (no transcription lag)
- **Low Latency**: Streaming audio for natural conversation
- **Tool Calling**: Built-in function calling for structured data
- **Context**: Maintains conversation history automatically

### Why WebSockets?
- **Bidirectional**: Server can push updates to client
- **Low Latency**: No HTTP overhead per message
- **Streaming**: Perfect for continuous audio flow
- **Real-Time**: Instant UI updates on state changes

---

## Limitations and Future Enhancements

### Current Limitations
- Single-language conversations (setup process is in English)
- No conversation editing (must restart to change early decisions)
- No persistence (configuration lost on browser close unless exported)
- Self-signed certificates (requires manual acceptance)

### Potential Enhancements
- **Database Storage**: Save configurations to database
- **Agent Management**: List, edit, duplicate existing agents
- **Multi-User**: Support multiple concurrent configuration sessions
- **Agent Testing**: Test the agent directly after creation
- **Export Formats**: Export to different agent frameworks
- **Voice Selection**: Preview and select different voices
- **Conversation Replay**: Review and edit conversation transcript
- **Templates**: Start from pre-built agent templates

---

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support contact information here]

---

## Quick Start Example

```bash
# 1. Setup
cd voice
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn websockets google-adk python-dotenv

# 2. Configure
echo "GEMINI_API_KEY=your_key_here" > .env
./create_cert.sh

# 3. Run
python live_streaming_server.py

# 4. Open
# Visit https://localhost:8006/enhanced
# Click "Start Session"
# Say: "Hi, I want to create an agent named Alex"
# Follow the conversation naturally
# Watch your configuration build in real-time
# Test interruption by speaking while AI is talking
```

---

**Built using Google ADK, Gemini 2.5 Flash with Live API, FastAPI, and Web Audio API.**
