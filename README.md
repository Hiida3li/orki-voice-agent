# Orki Voice Agent

> Build AI voice agents through natural conversation.

## What is This?

Orki Voice Agent is an agent that demonstrates how businesses can configure their AI customer service agents through a simple voice conversation instead of filling out complex forms.

**The idea**: Instead of clicking through settings and typing configurations, you simply *talk* to an AI that guides you through the setup process - just like having a conversation with a colleague.

## The Problem We're Solving

Setting up AI agents typically requires:
- Filling out lengthy forms
- Understanding technical jargon
- Multiple back-and-forth with support teams
- Time-consuming configuration processes

**Our approach**: Have a friendly AI assistant guide you through the entire setup via voice conversation in your preferred language and dialect.

## Use Cases

This POC demonstrates a pattern that can be applied to many industries:

### Call Centers
- Configure customer service bots through voice
- Set up IVR flows by describing them naturally
- Train agents on brand voice by giving examples verbally

### Customer Support
- Create support agents that match your company's tone
- Define escalation triggers conversationally
- Set up multilingual support with dialect preferences

### Sales Teams
- Build sales qualification bots through conversation
- Define lead scoring criteria naturally
- Configure follow-up workflows verbally

### Healthcare
- Set up appointment booking assistants
- Configure patient intake flows
- Define triage protocols conversationally

### Hospitality
- Create booking agents with specific personality
- Set up FAQ responses through examples
- Configure multilingual concierge services

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. Enter your website URL                                  │
│     (AI extracts your business context automatically)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Have a voice conversation                               │
│     - AI greets you and asks questions one by one           │
│     - Speaks in your language/dialect                       │
│     - You see configuration building in real-time           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Get your configured agent                               │
│     - Name, personality, language settings                  │
│     - Conversation flow defined                             │
│     - Brand voice examples captured                         │
│     - Handover triggers set                                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Voice-to-Voice**: Full duplex audio conversation with the AI
- **Dialect Support**: Supports Gulf Arabic dialects (Omani, Saudi, Emirati, etc.)
- **Real-time UI**: See your configuration build as you speak
- **Business Context**: Automatically extracts info from your website
- **Interruption Handling**: Natural conversation flow - interrupt anytime
- **Multi-language**: English, Arabic, Hindi, Urdu

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/orki-voice-agent.git
cd orki-voice-agent

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your GOOGLE_API_KEY to .env

# Run
python -m voice_agent
# Open http://localhost:8000
```

## Configuration Options

The AI collects these settings through conversation:

| Setting | Description |
|---------|-------------|
| **Agent Name** | What to call your AI agent |
| **Personality** | Friendly, Professional, Casual, etc. |
| **Languages** | Which languages to support |
| **Dialect** | Specific Arabic dialect (Gulf region) |
| **Conversation Flow** | Steps your agent should follow |
| **Brand Examples** | Sample conversations for tone matching |
| **Handover Triggers** | When to transfer to human |

## Tech Stack

- **Backend**: FastAPI + Python
- **AI**: Google Gemini 2.5 Flash (Native Audio)
- **Real-time**: WebSockets
- **Frontend**: Vanilla HTML/JS

## Adapting for Your Use Case

This POC can be adapted for any scenario where you need to:

1. **Collect structured data** through conversation
2. **Configure complex systems** without technical UI
3. **Onboard users** in their native language/dialect
4. **Create personalized experiences** based on verbal input

### To customize:
1. Modify `config/agent_instructions.py` - Change the conversation flow
2. Update `tools/constants.py` - Add your own valid options
3. Edit `tools/configuration.py` - Add new data collection tools

## Roadmap

- [ ] More Arabic dialect support (Egyptian, Levantine)
- [ ] Voice cloning for brand consistency
- [ ] Integration with popular CRM/helpdesk platforms
- [ ] Multi-turn conversation memory
- [ ] Export to various agent platforms

## Contributing

This is a POC - contributions welcome! Areas that need work:

- **Voice Quality**: Better Arabic/Gulf accent support
- **Dialect Authenticity**: Native expressions and greetings
- **Integration**: Connect to real agent platforms
- **Testing**: More comprehensive test coverage

## Documentation

For technical implementation details, see [TECHNICAL_DOCS.md](./TECHNICAL_DOCS.md)

## License

MIT

---

**Built with Google ADK and Gemini** | Focused on MENA region businesses
