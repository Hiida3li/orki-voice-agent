# Voice-to-Voice AI Agent Configuration System - API Documentation

## Table of Contents
1. [HTTP REST Endpoints](#http-rest-endpoints)
2. [WebSocket Endpoints](#websocket-endpoints)
3. [WebSocket Message Protocol](#websocket-message-protocol)
4. [Tool Call System](#tool-call-system)
5. [Audio Format Specifications](#audio-format-specifications)
6. [Error Responses](#error-responses)

---

## HTTP REST Endpoints

### Base URL
```
https://localhost:8006
```

### 1. Root Endpoint
**Endpoint:** `/`
**Method:** `GET`
**Description:** Serves the main PCM Player interface
**Response:** HTML page

**Example:**
```bash
curl https://localhost:8006/
```

---

### 2. PCM Player Interface
**Endpoint:** `/pcm`
**Method:** `GET`
**Description:** Serves the PCM Player interface with high-quality audio
**Response:** HTML page with embedded JavaScript

**Example:**
```bash
curl https://localhost:8006/pcm
```

---

### 3. Enhanced UI Interface
**Endpoint:** `/enhanced`
**Method:** `GET`
**Description:** Serves the enhanced UI with real-time configuration display and tool call visualization
**Response:** HTML page from `enhanced_ui.html` file

**Example:**
```bash
curl https://localhost:8006/enhanced
```

---

### 4. Health Check
**Endpoint:** `/health`
**Method:** `GET`
**Description:** Returns server health status, active sessions, and configuration information

**Response Format:**
```json
{
  "status": "healthy",
  "active_sessions": 0,
  "agent": "streaming_assistant",
  "model": "gemini-live-2.5-flash-preview",
  "tools_enabled": 10,
  "tools": [
    "get_agent_name",
    "get_agent_gender",
    "get_personality",
    "get_languages",
    "get_dialect",
    "get_interaction_steps",
    "get_conversation_examples",
    "get_handover_reasons",
    "get_additional_instructions",
    "conversation_complete"
  ],
  "observability": {
    "phoenix_tracing": "active",
    "phoenix_enabled": true,
    "phoenix_project": "adk-voice-agent"
  }
}
```

**Example:**
```bash
curl https://localhost:8006/health
```

---

## WebSocket Endpoints

### 1. Main WebSocket Connection
**Endpoint:** `/ws/{user_id}`
**Protocol:** WSS (WebSocket Secure)
**Query Parameters:**
- `is_audio`: `"true"` or `"false"` (default: `"true"`)

**Description:** Establishes bidirectional real-time communication for audio streaming and state updates

**Connection URL Format:**
```
wss://localhost:8006/ws/{user_id}?is_audio=true
```

**Example (JavaScript):**
```javascript
const ws = new WebSocket('wss://localhost:8006/ws/client_123?is_audio=true');
```

---

### 2. Live Audio WebSocket
**Endpoint:** `/ws/live/{client_id}`
**Protocol:** WSS (WebSocket Secure)
**Description:** Dedicated endpoint for live audio streaming (always uses audio mode)

**Connection URL Format:**
```
wss://localhost:8006/ws/live/{client_id}
```

**Example (JavaScript):**
```javascript
const ws = new WebSocket('wss://localhost:8006/ws/live/client_123');
```

---

## WebSocket Message Protocol

### Client to Server Messages

#### 1. Audio Data (PCM)
**Purpose:** Send user's microphone audio to the server

**Message Format:**
```json
{
  "mime_type": "audio/pcm",
  "data": "base64_encoded_audio_chunk"
}
```

**Audio Specifications:**
- Sample rate: 16kHz
- Channels: Mono (1)
- Bit depth: 16-bit
- Encoding: PCM
- Format: Int16 Little Endian
- Transport: Base64 encoded

**Example (JavaScript):**
```javascript
const pcmData = new Int16Array(4096); // 4096 samples
const buffer = pcmData.buffer;
const uint8Array = new Uint8Array(buffer);
const base64Audio = btoa(String.fromCharCode(...uint8Array));

ws.send(JSON.stringify({
  mime_type: 'audio/pcm',
  data: base64Audio
}));
```

---

#### 2. Text Input
**Purpose:** Send text message to the agent

**Message Format:**
```json
{
  "mime_type": "text/plain",
  "data": "User's text message"
}
```

**Example (JavaScript):**
```javascript
ws.send(JSON.stringify({
  mime_type: 'text/plain',
  data: 'Hello, I want to create an agent'
}));
```

---

#### 3. User Speaking Signal
**Purpose:** Notify server that user started speaking (for interruption handling)

**Message Format:**
```json
{
  "type": "user_speaking"
}
```

**Example (JavaScript):**
```javascript
ws.send(JSON.stringify({
  type: 'user_speaking'
}));
```

---

#### 4. Keepalive Ping
**Purpose:** Keep WebSocket connection alive

**Message Format:**
```json
{
  "type": "ping"
}
```

**Expected Response:**
```json
{
  "type": "pong"
}
```

---

### Server to Client Messages

#### 1. Connection Confirmation
**Purpose:** Confirm WebSocket connection established

**Message Format:**
```json
{
  "connected": true,
  "session_id": "session_abc123",
  "audio_enabled": true
}
```

**Fields:**
- `connected`: Boolean indicating successful connection
- `session_id`: Unique session identifier
- `audio_enabled`: Whether audio mode is active

---

#### 2. Audio Data (AI Response)
**Purpose:** Stream AI-generated audio to client

**Message Format:**
```json
{
  "mime_type": "audio/pcm;rate=24000",
  "data": "base64_encoded_audio_chunk"
}
```

**Audio Specifications:**
- Sample rate: 24kHz
- Channels: Mono (1)
- Bit depth: 16-bit
- Encoding: PCM
- Format: Int16 Little Endian
- Transport: Base64 encoded

**Example (JavaScript - Receiving):**
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.mime_type && data.mime_type.includes('audio/pcm')) {
    const binaryString = atob(data.data);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const int16Array = new Int16Array(bytes.buffer);
    pcmPlayer.feed(int16Array.buffer);
  }
};
```

---

#### 3. Text Response
**Purpose:** Send AI text response to client

**Message Format:**
```json
{
  "mime_type": "text/plain",
  "data": "AI's text message",
  "partial": false
}
```

**Fields:**
- `mime_type`: Always `"text/plain"`
- `data`: The text content
- `partial`: Boolean indicating if this is a partial response (streaming)

---

#### 4. Tool Call Notification
**Purpose:** Notify client that AI called a tool

**Message Format:**
```json
{
  "type": "tool_call",
  "tool_name": "get_agent_name",
  "tool_id": "call_abc123",
  "arguments": {
    "agent_name": "Maya"
  }
}
```

**Fields:**
- `type`: Always `"tool_call"`
- `tool_name`: Name of the tool being called
- `tool_id`: Unique identifier for this tool call
- `arguments`: Object containing tool arguments

---

#### 5. Tool Result
**Purpose:** Send tool execution result to client

**Message Format:**
```json
{
  "type": "tool_result",
  "tool_name": "get_agent_name",
  "tool_id": "call_abc123",
  "result": {
    "status": "success",
    "message": "Agent name set successfully",
    "agent_name": "Maya",
    "next_step": "Determine agent gender"
  }
}
```

**Fields:**
- `type`: Always `"tool_result"`
- `tool_name`: Name of the tool
- `tool_id`: Matching tool call ID
- `result`: Object containing tool execution result

---

#### 6. State Update
**Purpose:** Broadcast updated conversation state to client

**Message Format:**
```json
{
  "type": "state_update",
  "conversation_state": {
    "agent_name": "Maya",
    "agent_gender": "Female",
    "personality": "Empathetic and Friendly",
    "languages": ["English", "Arabic"],
    "dialect": "Omani",
    "interaction_steps": [],
    "conversation_examples": [],
    "handover_reasons": [],
    "additional_instructions": "",
    "completed": false
  }
}
```

**Fields:**
- `type`: Always `"state_update"`
- `conversation_state`: Complete current configuration state

---

#### 7. Turn Complete
**Purpose:** Signal that AI finished its turn

**Message Format:**
```json
{
  "turn_complete": true
}
```

---

#### 8. Interruption Confirmation
**Purpose:** Confirm that interruption was processed

**Message Format:**
```json
{
  "interrupted": true
}
```

---

#### 9. Error Message
**Purpose:** Report error to client

**Message Format:**
```json
{
  "error": "Error message description"
}
```

---

## Tool Call System

### Available Tools

#### 1. get_agent_name
**Purpose:** Capture agent's name

**Input:**
```json
{
  "agent_name": "Maya"
}
```

**Output:**
```json
{
  "status": "success",
  "message": "Agent name set successfully",
  "agent_name": "Maya",
  "next_step": "Determine agent gender"
}
```

---

#### 2. get_agent_gender
**Purpose:** Set agent's gender

**Input:**
```json
{
  "gender": "Female"
}
```

**Valid Values:** `"Male"`, `"Female"`

**Output:**
```json
{
  "status": "success",
  "message": "Agent gender set successfully",
  "gender": "Female",
  "next_step": "Define personality"
}
```

---

#### 3. get_personality
**Purpose:** Define agent's personality

**Input:**
```json
{
  "personality": "Empathetic and Friendly"
}
```

**Valid Values:**
- `"Empathetic and Friendly"`
- `"Formal and Professional"`
- `"Salesperson"`
- `"Fun and Humorous"`
- `"Casual and Down-To-Earth"`

**Output:**
```json
{
  "status": "success",
  "message": "Personality set successfully",
  "personality": "Empathetic and Friendly",
  "next_step": "Define languages"
}
```

---

#### 4. get_languages
**Purpose:** Specify supported languages

**Input:**
```json
{
  "languages": ["English", "Arabic"]
}
```

**Valid Values:** `"English"`, `"Arabic"`, `"Hindi"`, `"Urdu"`

**Output:**
```json
{
  "status": "success",
  "message": "Languages set successfully",
  "languages": ["English", "Arabic"],
  "requires_dialect": true,
  "next_step": "Specify Arabic dialect"
}
```

**Note:** `requires_dialect` is `true` only if Arabic is selected

---

#### 5. get_dialect
**Purpose:** Specify Arabic dialect (required if Arabic is selected)

**Input:**
```json
{
  "dialect": "Omani"
}
```

**Valid Values:**
- `"Omani"`
- `"Saudi"`
- `"Bahraini"`
- `"Kuwaiti"`
- `"Qatari"`
- `"Emirati"`
- `"Fusha (MSA)"`

**Output:**
```json
{
  "status": "success",
  "message": "Dialect set successfully",
  "dialect": "Omani",
  "next_step": "Define interaction steps"
}
```

---

#### 6. get_interaction_steps
**Purpose:** Define agent's conversation workflow

**Input:**
```json
{
  "interaction_steps": [
    "Greet customer warmly",
    "Ask what they need",
    "Collect necessary information",
    "Provide solution"
  ]
}
```

**Constraints:**
- Array of strings
- Recommended: 2-5 steps
- Each step should be a clear action

**Output:**
```json
{
  "status": "success",
  "message": "Interaction steps captured successfully",
  "interaction_steps": [
    "Greet customer warmly",
    "Ask what they need",
    "Collect necessary information",
    "Provide solution"
  ],
  "next_step": "Capture conversation examples"
}
```

---

#### 7. get_conversation_examples
**Purpose:** Capture brand voice through example dialogues

**Input:**
```json
{
  "conversation_examples": [
    {
      "customer_message": "Do you deliver?",
      "agent_response": "Yes, we deliver nationwide! When would you like your order?"
    },
    {
      "customer_message": "What are your business hours?",
      "agent_response": "We're open 9 AM to 6 PM, Sunday to Thursday."
    }
  ]
}
```

**Constraints:**
- Array of objects
- Each object must have `customer_message` and `agent_response`
- Recommended: 2-5 examples

**Output:**
```json
{
  "status": "success",
  "message": "Conversation examples captured successfully",
  "conversation_examples": [...],
  "next_step": "Define handover reasons"
}
```

---

#### 8. get_handover_reasons
**Purpose:** Define when AI should escalate to human

**Input:**
```json
{
  "handover_reasons": [
    {
      "reason": "Customer Frustration",
      "description": "When customer expresses anger or frustration multiple times"
    },
    {
      "reason": "Manager Request",
      "description": "When customer explicitly asks for a manager"
    }
  ]
}
```

**Constraints:**
- Array of objects
- Each object must have `reason` and `description`
- Recommended: 2-5 reasons

**Output:**
```json
{
  "status": "success",
  "message": "Handover reasons captured successfully",
  "handover_reasons": [...],
  "next_step": "Provide additional instructions if needed"
}
```

---

#### 9. get_additional_instructions
**Purpose:** Capture custom behavioral rules

**Input:**
```json
{
  "instructions": "Always offer a discount code if customers seem hesitant"
}
```

**Constraints:**
- String
- Maximum: 2000 characters (warning if exceeded)

**Output:**
```json
{
  "status": "success",
  "message": "Additional instructions set successfully",
  "instructions": "Always offer a discount code if customers seem hesitant",
  "next_step": "Ask if user is done configuring"
}
```

---

#### 10. conversation_complete
**Purpose:** Mark conversation as complete

**Input:**
```json
{
  "reason": "User said that's all"
}
```

**Output:**
```json
{
  "status": "success",
  "message": "Configuration completed successfully",
  "completed": true,
  "final_config": {
    "agent_name": "Maya",
    "agent_gender": "Female",
    "personality": "Empathetic and Friendly",
    "languages": ["English", "Arabic"],
    "dialect": "Omani",
    "interaction_steps": [...],
    "conversation_examples": [...],
    "handover_reasons": [...],
    "additional_instructions": "...",
    "completion_reason": "User said that's all",
    "completed_at": "2025-10-14T12:34:56.789012"
  }
}
```

---

## Audio Format Specifications

### Client → Server (Microphone Input)

**Format:**
```
Sample Rate: 16000 Hz (16 kHz)
Channels: 1 (Mono)
Bit Depth: 16-bit
Encoding: PCM (Pulse Code Modulation)
Format: Int16 Little Endian
Transport: Base64 encoded via WebSocket JSON
Chunk Size: 4096 samples (256 KB per chunk)
```

**JavaScript Conversion:**
```javascript
// Float32Array from Web Audio API → Int16Array
const inputData = audioProcessingEvent.inputBuffer.getChannelData(0); // Float32
const pcmData = new Int16Array(inputData.length);

for (let i = 0; i < inputData.length; i++) {
  const s = Math.max(-1, Math.min(1, inputData[i])); // Clamp
  pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;      // Convert to Int16
}

// Convert to ArrayBuffer
const buffer = new ArrayBuffer(pcmData.length * 2);
const view = new DataView(buffer);
for (let i = 0; i < pcmData.length; i++) {
  view.setInt16(i * 2, pcmData[i], true); // true = little endian
}

// Base64 encode
const uint8Array = new Uint8Array(buffer);
const base64Audio = btoa(String.fromCharCode(...uint8Array));
```

---

### Server → Client (AI Audio Output)

**Format:**
```
Sample Rate: 24000 Hz (24 kHz)
Channels: 1 (Mono)
Bit Depth: 16-bit
Encoding: PCM (Pulse Code Modulation)
Format: Int16 Little Endian
Transport: Base64 encoded via WebSocket JSON
```

**JavaScript Decoding:**
```javascript
// Decode base64
const binaryString = atob(base64Data);
const len = binaryString.length;
const bytes = new Uint8Array(len);
for (let i = 0; i < len; i++) {
  bytes[i] = binaryString.charCodeAt(i);
}

// Convert to Int16Array
const int16Array = new Int16Array(bytes.buffer);

// Feed to PCM Player
pcmPlayer.feed(int16Array.buffer);
```

---

## Error Responses

### WebSocket Connection Errors

#### Authentication Error
```json
{
  "error": "Authentication failed",
  "code": "AUTH_ERROR"
}
```

#### Session Creation Error
```json
{
  "error": "Failed to create session",
  "code": "SESSION_ERROR"
}
```

#### Audio Processing Error
```json
{
  "error": "Audio processing failed: Invalid format",
  "code": "AUDIO_ERROR"
}
```

---

### Tool Call Errors

#### Validation Error
```json
{
  "type": "tool_result",
  "tool_name": "get_personality",
  "tool_id": "call_123",
  "result": {
    "status": "error",
    "message": "Invalid personality. Must be one of: Empathetic and Friendly, Formal and Professional, Salesperson, Fun and Humorous, Casual and Down-To-Earth",
    "error_code": "VALIDATION_ERROR"
  }
}
```

#### Missing Required Field
```json
{
  "type": "tool_result",
  "tool_name": "get_agent_name",
  "tool_id": "call_123",
  "result": {
    "status": "error",
    "message": "Agent name is required",
    "error_code": "MISSING_FIELD"
  }
}
```

#### Character Limit Exceeded
```json
{
  "type": "tool_result",
  "tool_name": "get_additional_instructions",
  "tool_id": "call_123",
  "result": {
    "status": "warning",
    "message": "Instructions exceed 2000 characters (2150 characters). Consider shortening.",
    "instructions": "...",
    "character_count": 2150
  }
}
```

---

## Rate Limits and Constraints

### WebSocket Connection
- Maximum concurrent connections: 100 (configurable)
- Maximum message size: 10 MB
- Keepalive interval: 5 seconds
- Connection timeout: 30 seconds (no activity)

### Audio Streaming
- Maximum audio chunk size: 512 KB
- Minimum buffer size: 2 chunks
- Buffer timeout: 300ms
- Maximum audio queue: 50 chunks

### Tool Calls
- No rate limiting on tool calls
- Maximum concurrent tool executions: 10 per session
- Tool execution timeout: 30 seconds

---

## Example Integration

### Complete Frontend Integration Example

```javascript
class VoiceAgentClient {
  constructor() {
    this.ws = null;
    this.pcmPlayer = null;
    this.audioContext = null;
    this.isConnected = false;
  }

  connect(userId) {
    const wsUrl = `wss://localhost:8006/ws/${userId}?is_audio=true`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Connected to server');
      this.isConnected = true;
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected from server');
      this.isConnected = false;
    };
  }

  handleMessage(data) {
    if (data.connected) {
      console.log('Session ID:', data.session_id);
      this.startAudioCapture();
    }
    else if (data.mime_type === 'audio/pcm') {
      this.playAudio(data.data);
    }
    else if (data.type === 'tool_call') {
      console.log('Tool called:', data.tool_name, data.arguments);
    }
    else if (data.type === 'tool_result') {
      console.log('Tool result:', data.result);
    }
    else if (data.type === 'state_update') {
      this.updateUI(data.conversation_state);
    }
    else if (data.turn_complete) {
      console.log('Turn complete');
    }
    else if (data.interrupted) {
      console.log('Interrupted');
      this.stopAudioPlayback();
    }
  }

  sendAudio(pcmData) {
    const base64Audio = this.encodeAudio(pcmData);
    this.ws.send(JSON.stringify({
      mime_type: 'audio/pcm',
      data: base64Audio
    }));
  }

  sendText(message) {
    this.ws.send(JSON.stringify({
      mime_type: 'text/plain',
      data: message
    }));
  }

  sendInterruption() {
    this.ws.send(JSON.stringify({
      type: 'user_speaking'
    }));
  }

  encodeAudio(pcmData) {
    const buffer = new ArrayBuffer(pcmData.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < pcmData.length; i++) {
      view.setInt16(i * 2, pcmData[i], true);
    }
    const uint8Array = new Uint8Array(buffer);
    return btoa(String.fromCharCode(...uint8Array));
  }

  playAudio(base64Data) {
    const binaryString = atob(base64Data);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    const int16Array = new Int16Array(bytes.buffer);
    this.pcmPlayer.feed(int16Array.buffer);
  }

  updateUI(state) {
    // Update your UI with the new state
    console.log('Configuration updated:', state);
  }

  stopAudioPlayback() {
    if (this.pcmPlayer) {
      this.pcmPlayer.destroy && this.pcmPlayer.destroy();
      this.initPCMPlayer();
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const client = new VoiceAgentClient();
client.connect('user_123');
```

---

## Testing APIs

### Using cURL

**Health Check:**
```bash
curl -k https://localhost:8006/health
```

**WebSocket Test (requires wscat):**
```bash
npm install -g wscat
wscat -c "wss://localhost:8006/ws/test_user?is_audio=true" --no-check
```

### Using Postman

1. Create new request
2. Set method to GET
3. Enter URL: `https://localhost:8006/health`
4. Disable SSL verification (for self-signed cert)
5. Send request

### Using Browser Console

```javascript
const ws = new WebSocket('wss://localhost:8006/ws/test_user?is_audio=true');

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);

// Send ping
ws.send(JSON.stringify({ type: 'ping' }));
```

---

## Security Considerations

### SSL/TLS
- All connections must use HTTPS/WSS
- Self-signed certificates accepted for local development
- Production should use valid CA-signed certificates

### Authentication
- Currently no authentication required (local development)
- Production should implement:
  - API key authentication
  - JWT tokens
  - Rate limiting per user

### Data Privacy
- Audio data transmitted in real-time, not stored
- Conversation outputs saved to `conversation_outputs/` directory
- No audio recordings saved by default

---

## Version Information

**API Version:** 1.0.0
**Last Updated:** 2025-10-14
**Server Version:** See `/health` endpoint
**Compatibility:** Modern browsers with WebSocket and Web Audio API support
