"""
ADK Live Streaming Server - Standard Setup
Following ADK documentation patterns for custom streaming WebSocket
"""

import asyncio
import base64
import json
import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Phoenix tracing (must be done early, before ADK imports)
from phoenix_config import setup_phoenix_tracing, get_phoenix_info
phoenix_tracer = setup_phoenix_tracing()

# ADK imports - following documentation pattern
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai.types import (
    Content,
    Part,
    Blob,
    SpeechConfig,
    VoiceConfig,
    PrebuiltVoiceConfig
)

# Import tools
from tools import all_tools

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verify API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY is required")

# Create FastAPI app
app = FastAPI(title="ADK Streaming Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK components (following documentation pattern)
logger.info("Initializing agent with tools...")
logger.info(f"Number of tools: {len(all_tools)}")
for tool in all_tools:
    logger.info(f"  Tool: {tool}")

# Agent instruction template with placeholders for business context
AGENT_INSTRUCTION_TEMPLATE = """# 1. Persona

You are a friendly, patient, and tech-savvy Onboarding Specialist for Orki, a SaaS platform that helps MENA businesses boost their sales with AI agents. Your personality is warm, conversational, and genuinely helpful. Imagine you're having a virtual coffee chat with a new business owner, guiding them through the exciting process of creating their first AI agent. Your goal is to make this technical setup feel effortless, creative, and collaborative. Avoid corporate jargon and robotic phrases; instead, use natural, encouraging language.

# 2. Primary Objective

Your mission is to guide the user through a single, seamless voice conversation to fully configure their new customer-facing AI agent. You will collect all the necessary details by asking simple, one-at-a-time questions, making the user feel supported and confident throughout the process.

# 3. Contextual Information

You have been provided with key details about the user's business. Use this information to personalize the conversation and provide intelligent, relevant suggestions.

{business_context_section}

# 4. Core Principles of Interaction

These are the foundational behaviors that define your persona.

* **Be Proactive, Not Passive:** You always speak first. Greet the user warmly{company_greeting}. Your opening line should immediately transition to asking about their language preference.
    > **Example:** "Hi there! I'm here to help you get your AI agent set up{company_mention}. To make this as easy as possible, what language would you prefer to chat in?"

* **Be a Linguistic Chameleon (The Mirroring Protocol):** This is your most important skill.
    * **Listen First:** After you ask for their language, pay close attention to the *exact* words, dialect, and level of formality they use.
    * **Mirror Immediately:** Instantly switch to their communication style. If they speak casually in an Egyptian dialect, you do too. If they are formal in British English, you adopt that style.
    * **Be Adaptive:** Don't ask them to clarify their dialect. Simply mirror what you hear. You are a reflection of their natural speech.

* **Speak Like a Human:**
    * **Brevity is Key:** Keep your sentences short and to the point. Aim for 1-2 sentences per turn.
    * **One Thing at a Time:** Never ask more than one question at once.
    * **Stay Casual:** Use contractions (e.g., "let's," "you're," "what's") and a friendly tone.

* **Be an Active Listener (Graceful Interruptions):** If a user answers your question before you've finished asking or presenting options, **do not repeat yourself.** Immediately and smoothly accept their answer and move to the next step. Treat their interruption as the definitive answer.

* **Trust the UI (No Redundant Confirmations):** The user can see their selections appearing on their screen in real-time. **Do not verbally confirm what you have captured.** After they provide a piece of information, transition directly to the next question.
    > **BAD:** "Great, I've set the agent's name to 'SalesBot'. Now, what personality..."
    >
    > **GOOD:** "Perfect. Now for the personality..."

# 5. The Onboarding Journey (Conversation Flow)

Follow this sequence to build the agent. Use the contextual information to offer smart suggestions where appropriate.

**Step 1: The Welcome & Agent's Identity**
* Deliver your proactive, personalized greeting.
* Once the language is set, ask what they'd like to **name their agent.**
* Based on the name, silently determine if it's typically masculine or feminine and record the gender.

**Step 2: Defining the Personality**
* Briefly explain that personality shapes the agent's tone.
* Offer the following choices: **Empathetic & Friendly, Formal & Professional, Salesperson, Fun & Humorous, or Casual & Down-to-Earth.**
* **Suggest a starting point** based on their business{business_suggestion}.
    > **Example:** "Based on your business, a **Formal & Professional** personality might be a great fit for your customers. Does that sound right, or would you prefer another style?"
* **Do not be too rigid** and automatically and intelligently map to one of the valid choices if their preference doesn't exactly match the available options.
**Step 3: Setting the Dialect**
* Tell the user that Orki's AI agents can speak many languages, but ask them which dialect of Arabic would they like the AI agent to respond in?

**Step 4: Mapping the Customer Conversation**
* Guide them to outline 2-5 simple steps for the agent's customer interaction flow.
* **Offer a tailored suggestion** to get them started.
    > **Example:** "Let's think about the ideal conversation flow. For a business like yours, a good starting point could be: 1. Greet the customer and ask how you can help, 2. Answer their question using the knowledge base, and 3. Ask if they need anything else. How does that sound?"

**Step 5: Capturing the Brand's Voice (Optional)**
* Explain that providing a few conversation examples can help the AI perfectly match their brand's tone. Ask if they'd like to add 2-3 examples now. If not, assure them they can skip it.

**Step 6: Setting Up Safety Nets (Optional)**
* Explain that handover triggers allow the AI to seamlessly pass a conversation to a human. Ask if they want to set up a few common reasons, like when a customer asks for a person or seems frustrated. If not, move on.

**Step 7: Adding the Final Touches (Optional)**
* Ask a simple, open-ended question for any final details.
    > **Example:** "Great, we're almost done. Are there any other special instructions you have for the agent?"

**Step 8: The Wrap-up**
* Once all steps are complete, confirm if they're happy with the setup. When they confirm they are finished, thank them and end the call.
    > **Example:** "That's everything. Your new AI agent is configured and ready to go! It was a pleasure building it with you. Have a great day!"""


def create_agent_with_context(business_context: Optional[Dict[str, Any]] = None) -> Agent:
    """Create an agent with business context baked into the instruction"""

    if business_context:
        company_name = business_context.get('company_name', 'Unknown')
        description = business_context.get('description', '')
        faqs = business_context.get('faqs', [])

        # Build business context section
        business_section = f"""* **Company Name:** {company_name}
* **Company Description:** {description}"""

        if faqs:
            business_section += "\n* **Business FAQs:**\n"
            for i, faq in enumerate(faqs[:10], 1):
                question = faq.get('question', '')
                answer = faq.get('answer', '')
                business_section += f"  {i}. Q: {question}\n     A: {answer}\n"

        # Fill in the template
        instruction = AGENT_INSTRUCTION_TEMPLATE.format(
            business_context_section=business_section,
            company_greeting=f" and mention their company ({company_name}) to show you're prepared",
            company_mention=f" for {company_name}",
            business_suggestion=f" (consider that they operate {description})"
        )

        logger.info(f" Created agent with business context for: {company_name}")
    else:
        # No business context - use generic placeholders
        business_section = """* **Company Name:** [To be determined]
* **Company Description:** [To be provided by user]
* **Business FAQs:** [No FAQs available yet]"""

        instruction = AGENT_INSTRUCTION_TEMPLATE.format(
            business_context_section=business_section,
            company_greeting="",
            company_mention="",
            business_suggestion=""
        )

        logger.info("Created agent without business context (generic)")

    # Create agent with the filled instruction
    agent = Agent(
        model='gemini-2.5-flash-native-audio-latest',
        name='agent_config_collector',
        instruction=instruction,
        tools=all_tools
    )

    return agent


# Create default agent (without business context)
default_agent = create_agent_with_context(business_context=None)

# Create default runner with default agent
default_runner = InMemoryRunner(
    app_name="adk_streaming_app",
    agent=default_agent
)

# Session management
active_sessions: Dict[str, Dict[str, Any]] = {}


# Pydantic models for API requests
class BusinessContextRequest(BaseModel):
    website_url: str


async def extract_business_context(website_url: str) -> Dict[str, Any]:
    """
    Extract business context from a website URL using LLM.

    Extracts:
    - Company name
    - Description
    - FAQs (LLM-generated based on content)
    """
    context = {
        "company_name": "",
        "description": "",
        "faqs": []
    }

    try:
        # Fetch the website content with timeout
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = await client.get(website_url, headers=headers)
            response.raise_for_status()

            # Extract text content from HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text content (limit to first 8000 chars to stay within token limits)
            text_content = soup.get_text(separator='\n', strip=True)
            text_content = text_content[:8000]

            # Get page title for additional context
            title = soup.find('title')
            page_title = title.string.strip() if title and title.string else ""

            logger.info(f"Extracted {len(text_content)} characters from {website_url}")

            # Use Gemini to extract structured information
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            prompt = f"""Analyze the following website content and extract business information.

Website URL: {website_url}
Page Title: {page_title}

Website Content:
{text_content}

Please provide:
1. Company/Business Name (extract the main business name, not generic terms)
2. Brief Description (1-2 sentences about what the business does)
3. Generate 5-8 relevant FAQs that customers might ask about this business

Respond in this exact JSON format:
{{
  "company_name": "Business Name Here",
  "description": "Brief description of the business",
  "faqs": [
    {{"question": "FAQ question 1?", "answer": "Clear answer to the question"}},
    {{"question": "FAQ question 2?", "answer": "Clear answer to the question"}}
  ]
}}

Important:
- company_name should be the actual business name, not generic terms like "Home", "Website", etc.
- description should be concise and informative
- FAQs should be realistic questions customers would ask
- Keep answers clear and helpful
"""

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            # Parse the JSON response
            result_text = response.text.strip()
            extracted_data = json.loads(result_text)

            # Update context with extracted data
            context['company_name'] = extracted_data.get('company_name', 'Unknown')
            context['description'] = extracted_data.get('description', '')
            context['faqs'] = extracted_data.get('faqs', [])[:10]  # Limit to 10 FAQs

            logger.info(f"✅ LLM extracted: '{context['company_name']}' with {len(context['faqs'])} FAQs")

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching {website_url}")
        context['error'] = 'Request timeout'
        context['company_name'] = 'Unknown'
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {website_url}: {e}")
        context['error'] = f'HTTP {e.response.status_code}'
        context['company_name'] = 'Unknown'
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing LLM response: {e}")
        context['error'] = 'Failed to parse LLM response'
        context['company_name'] = 'Unknown'
    except Exception as e:
        logger.error(f"Error extracting business context from {website_url}: {e}", exc_info=True)
        context['error'] = str(e)
        context['company_name'] = 'Unknown'

    return context


async def save_conversation_json(user_id: str, session_id: str,
                                 conversation_state: Dict[str, Any],
                                 tool_results_log: list):
    """Save the conversation state and tool results to a JSON file"""
    import datetime

    # Create output directory if it doesn't exist
    output_dir = "conversation_outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/agent_config_{user_id}_{timestamp}.json"

    # Prepare final JSON structure
    final_output = {
        "metadata": {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "completed": conversation_state.get('completed', False)
        },
        "agent_configuration": {
            "agent_name": conversation_state.get('agent_name', ''),
            "agent_gender": conversation_state.get('agent_gender', ''),
            "personality": conversation_state.get('personality', ''),
            "languages": conversation_state.get('languages', []),
            "dialect": conversation_state.get('dialect', ''),
            "interaction_steps": conversation_state.get('interaction_steps', []),
            "conversation_examples": conversation_state.get('conversation_examples', []),
            "handover_reasons": conversation_state.get('handover_reasons', []),
            "additional_instructions": conversation_state.get('additional_instructions', ''),
            "completion_reason": conversation_state.get('completion_reason', '')
        },
        "tool_execution_log": tool_results_log,
        "full_conversation_state": conversation_state
    }

    # Write to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        logger.info(f"Conversation saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving conversation JSON: {e}", exc_info=True)
        return None


async def agent_to_client_messaging(websocket: WebSocket, live_queue: LiveRequestQueue,
                                   run_config: RunConfig, user_id: str, session_id: str, runner: InMemoryRunner):
    """Handle agent responses and send to client WITHOUT buffering for instant interruption"""
    # REMOVED BUFFERING for instant interruption - audio sent immediately

    # Interruption handling - using shared flag from active_sessions
    is_agent_speaking = False

    # Conversation state tracking
    conversation_state = {}
    tool_results_log = []

    async def safe_send_json(data: dict) -> bool:
        """Safely send JSON data, return False if connection is closed"""
        try:
            # Check if WebSocket is still connected
            if websocket.client_state.name != "CONNECTED":
                return False
            await websocket.send_json(data)
            return True
        except RuntimeError as e:
            if "websocket.send" in str(e).lower():
                logger.debug(f"WebSocket already closed, skipping message")
                return False
            raise
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            return False


    try:
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_queue,
            run_config=run_config
        ):
            # Handle tool calls - check BOTH event attributes AND content.parts
            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    # Check for function_call in Part
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        tool_call_data = {
                            "type": "tool_call",
                            "tool_name": fc.name,
                            "tool_id": fc.id,
                            "arguments": fc.args if hasattr(fc, 'args') else {}
                        }

                        # Send tool call notification to frontend
                        if not await safe_send_json(tool_call_data):
                            return  # Connection closed
                        logger.info(f"🔧 Tool called: {fc.name} with args: {tool_call_data['arguments']}")

                    # Check for function_response in Part
                    if hasattr(part, 'function_response') and part.function_response:
                        fr = part.function_response
                        tool_result_data = {
                            "type": "tool_result",
                            "tool_name": fr.name,
                            "tool_id": fr.id,
                            "result": fr.response
                        }

                        # Log the tool result
                        tool_results_log.append({
                            "timestamp": asyncio.get_event_loop().time(),
                            "tool_name": fr.name,
                            "result": fr.response
                        })

                        # Update conversation state
                        if fr.response.get('status') == 'success':
                            tool_name = fr.name

                            # Extract the relevant data from tool result
                            if tool_name == 'get_agent_name':
                                conversation_state['agent_name'] = fr.response.get('agent_name')
                            elif tool_name == 'get_agent_gender':
                                conversation_state['agent_gender'] = fr.response.get('gender')
                            elif tool_name == 'get_personality':
                                conversation_state['personality'] = fr.response.get('personality')
                            elif tool_name == 'get_languages':
                                conversation_state['languages'] = fr.response.get('languages')
                            elif tool_name == 'get_dialect':
                                conversation_state['dialect'] = fr.response.get('dialect')
                            elif tool_name == 'get_interaction_steps':
                                steps = fr.response.get('interaction_steps')
                                logger.info(f"📝 Extracted interaction_steps: {steps}")
                                conversation_state['interaction_steps'] = steps
                                logger.info(f"📋 Updated conversation_state: {conversation_state}")
                            elif tool_name == 'get_conversation_examples':
                                examples = fr.response.get('conversation_examples')
                                logger.info(f"💬 Extracted conversation_examples: {examples}")
                                conversation_state['conversation_examples'] = examples
                                logger.info(f"📋 Updated conversation_state: {conversation_state}")
                            elif tool_name == 'get_handover_reasons':
                                handover_reasons = fr.response.get('handover_reasons')
                                logger.info(f"🔄 Extracted handover_reasons: {handover_reasons}")
                                conversation_state['handover_reasons'] = handover_reasons
                                logger.info(f"📋 Updated conversation_state: {conversation_state}")
                            elif tool_name == 'get_additional_instructions':
                                instructions = fr.response.get('instructions')
                                logger.info(f"📝 Extracted additional_instructions: {instructions}")
                                conversation_state['additional_instructions'] = instructions
                                logger.info(f"📋 Updated conversation_state: {conversation_state}")
                            elif tool_name == 'conversation_complete':
                                conversation_state['completed'] = True
                                conversation_state['completion_reason'] = fr.response.get('final_config', {}).get('completion_reason')

                        # Send tool result to frontend (for live UI updates)
                        if not await safe_send_json(tool_result_data):
                            return  # Connection closed

                        # Send updated conversation state
                        state_update_msg = {
                            "type": "state_update",
                            "conversation_state": conversation_state
                        }
                        logger.info(f"🔄 Sending state_update: {state_update_msg}")
                        if not await safe_send_json(state_update_msg):
                            return  # Connection closed

                        logger.info(f"✅ Tool result for {fr.name}: {fr.response}")

                        # If conversation complete, save JSON file
                        if fr.name == 'conversation_complete' and fr.response.get('completed'):
                            await save_conversation_json(user_id, session_id, conversation_state, tool_results_log)

            # LEGACY: Also check event-level attributes (might not be populated in live mode)
            if hasattr(event, 'function_calls') and event.function_calls:
                for function_call in event.function_calls:
                    logger.info(f"🔧 Event-level function_call: {function_call.name}")

            # LEGACY: Check event-level function responses
            if hasattr(event, 'function_responses') and event.function_responses:
                for function_response in event.function_responses:
                    tool_result_data = {
                        "type": "tool_result",
                        "tool_name": function_response.name,
                        "tool_id": function_response.id,
                        "result": function_response.response
                    }

                    # Log the tool result
                    tool_results_log.append({
                        "timestamp": asyncio.get_event_loop().time(),
                        "tool_name": function_response.name,
                        "result": function_response.response
                    })

                    # Update conversation state
                    if function_response.response.get('status') == 'success':
                        tool_name = function_response.name

                        # Extract the relevant data from tool result
                        if tool_name == 'get_agent_name':
                            conversation_state['agent_name'] = function_response.response.get('agent_name')
                        elif tool_name == 'get_agent_gender':
                            conversation_state['agent_gender'] = function_response.response.get('gender')
                        elif tool_name == 'get_personality':
                            conversation_state['personality'] = function_response.response.get('personality')
                        elif tool_name == 'get_languages':
                            conversation_state['languages'] = function_response.response.get('languages')
                        elif tool_name == 'get_dialect':
                            conversation_state['dialect'] = function_response.response.get('dialect')
                        elif tool_name == 'get_interaction_steps':
                            steps = function_response.response.get('interaction_steps')
                            logger.info(f"📝 [LEGACY] Extracted interaction_steps: {steps}")
                            conversation_state['interaction_steps'] = steps
                            logger.info(f"📋 [LEGACY] Updated conversation_state: {conversation_state}")
                        elif tool_name == 'get_conversation_examples':
                            examples = function_response.response.get('conversation_examples')
                            logger.info(f"💬 [LEGACY] Extracted conversation_examples: {examples}")
                            conversation_state['conversation_examples'] = examples
                            logger.info(f"📋 [LEGACY] Updated conversation_state: {conversation_state}")
                        elif tool_name == 'get_handover_reasons':
                            handover_reasons = function_response.response.get('handover_reasons')
                            logger.info(f"🔄 [LEGACY] Extracted handover_reasons: {handover_reasons}")
                            conversation_state['handover_reasons'] = handover_reasons
                            logger.info(f"📋 [LEGACY] Updated conversation_state: {conversation_state}")
                        elif tool_name == 'get_additional_instructions':
                            instructions = function_response.response.get('instructions')
                            logger.info(f"📝 [LEGACY] Extracted additional_instructions: {instructions}")
                            conversation_state['additional_instructions'] = instructions
                            logger.info(f"📋 [LEGACY] Updated conversation_state: {conversation_state}")
                        elif tool_name == 'conversation_complete':
                            conversation_state['completed'] = True
                            conversation_state['completion_reason'] = function_response.response.get('final_config', {}).get('completion_reason')

                    # Send tool result to frontend (for live UI updates)
                    if not await safe_send_json(tool_result_data):
                        return  # Connection closed

                    # Send updated conversation state
                    state_update_msg = {
                        "type": "state_update",
                        "conversation_state": conversation_state
                    }
                    logger.info(f"🔄 [LEGACY] Sending state_update: {state_update_msg}")
                    if not await safe_send_json(state_update_msg):
                        return  # Connection closed

                    logger.info(f"Tool result for {function_response.name}: {function_response.response}")

                    # If conversation complete, save JSON file
                    if function_response.name == 'conversation_complete' and function_response.response.get('completed'):
                        await save_conversation_json(user_id, session_id, conversation_state, tool_results_log)

            if hasattr(event, 'content') and event.content:
                content = event.content

                # Process parts in content
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        # Text response
                        if hasattr(part, 'text') and part.text:
                            if not await safe_send_json({
                                "mime_type": "text/plain",
                                "data": part.text,
                                "partial": getattr(event, 'partial', False)
                            }):
                                return  # Connection closed
                            logger.info(f"Sent text: {part.text[:50]}...")

                        # Audio response (inline_data)
                        if hasattr(part, 'inline_data') and part.inline_data:
                            inline_data = part.inline_data
                            if hasattr(inline_data, 'data') and hasattr(inline_data, 'mime_type'):
                                # Skip if interrupted - check shared flag
                                if active_sessions.get(user_id, {}).get("should_cancel_output", False):
                                    logger.debug(f"Skipping audio chunk - user interrupted")
                                    continue

                                # Mark agent as speaking
                                is_agent_speaking = True

                                # Send audio immediately without buffering for instant interruption
                                audio_chunk = {
                                    "mime_type": inline_data.mime_type,
                                    "data": base64.b64encode(inline_data.data).decode()
                                }

                                # Send immediately - no buffering
                                if not await safe_send_json(audio_chunk):
                                    return  # Connection closed

                                logger.debug(f"Sent audio chunk immediately ({len(inline_data.data)} bytes)")

            # Handle turn completion - no flushing needed (audio sent immediately)
            if hasattr(event, 'turn_complete') and event.turn_complete:
                is_agent_speaking = False
                # Reset shared interruption flags for next turn
                if user_id in active_sessions:
                    active_sessions[user_id]["should_cancel_output"] = False
                    active_sessions[user_id]["user_interrupted"] = False
                if not await safe_send_json({
                    "turn_complete": True
                }):
                    return  # Connection closed
                logger.info("Turn completed")

            # Handle interruption - stop output immediately
            if hasattr(event, 'interrupted') and event.interrupted:
                user_initiated = active_sessions.get(user_id, {}).get("user_interrupted", False)
                logger.info(f"⚠️ Interruption detected by ADK (user_initiated={user_initiated}) - stopping output")
                # Set shared flag to stop all output immediately
                if user_id in active_sessions:
                    active_sessions[user_id]["should_cancel_output"] = True
                is_agent_speaking = False
                # Send interruption signal to client
                if not await safe_send_json({
                    "interrupted": True
                }):
                    return  # Connection closed
                logger.info(f"✅ Interrupted - output stopped, ADK should now process new input in context")

    except Exception as e:
        logger.error(f"Error in agent messaging: {e}", exc_info=True)
        # Try to send error, but don't fail if connection is already closed
        await safe_send_json({
            "error": str(e)
        })


async def client_to_agent_messaging(websocket: WebSocket, live_queue: LiveRequestQueue,
                                   user_id: str):
    """Handle client messages and send to agent"""
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            mime_type = data.get("mime_type", "")
            content_data = data.get("data", "")

            if mime_type == "text/plain":
                # Text input
                content = Content(parts=[Part(text=content_data)])
                live_queue.send_content(content)
                logger.info(f"Client #{user_id} sent text: {content_data}")

            elif mime_type == "audio/pcm":
                # Audio input - decode base64 and send as blob
                audio_bytes = base64.b64decode(content_data)
                audio_blob = Blob(
                    mime_type="audio/pcm;rate=16000",
                    data=audio_bytes
                )
                live_queue.send_realtime(audio_blob)
                # Less verbose logging for audio
                logger.debug(f"Client #{user_id} sent audio: {len(audio_bytes)} bytes")

            elif data.get("type") == "user_speaking":
                # Client detected user started speaking
                # NOTE: We set the flag immediately for fast UX, but the ADK will also detect
                # the interruption naturally from the incoming audio stream
                logger.info(f"🎤 User #{user_id} started speaking - setting interruption flag")
                if user_id in active_sessions:
                    active_sessions[user_id]["should_cancel_output"] = True
                    active_sessions[user_id]["user_interrupted"] = True  # Track that user initiated interruption
                    logger.info(f"✋ Interruption flag set - stopping audio output immediately")

            elif data.get("type") == "ping":
                # Handle keepalive ping
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Client #{user_id} disconnected")
    except Exception as e:
        logger.error(f"Error in client messaging: {e}", exc_info=True)


async def start_agent_session(user_id: str, is_audio: bool = True, business_context: Optional[Dict[str, Any]] = None):
    """Initialize agent session following ADK documentation pattern"""

    # Create custom runner if business context provided, otherwise use default
    if business_context:
        # Create custom agent with business context baked in
        custom_agent = create_agent_with_context(business_context)
        custom_runner = InMemoryRunner(
            app_name="adk_streaming_app",
            agent=custom_agent
        )
        session_runner = custom_runner
        logger.info(f"✨ Using custom runner with business context for user {user_id}")
    else:
        session_runner = default_runner
        logger.info(f"Using default runner for user {user_id}")

    # Create session
    session = await session_runner.session_service.create_session(
        app_name="adk_streaming_app",
        user_id=user_id
    )

    # Configure run based on mode
    if is_audio:
        # Audio configuration
        speech_config = SpeechConfig(
            voice_config=VoiceConfig(
                prebuilt_voice_config=PrebuiltVoiceConfig(
                    voice_name="Charon",

                )
            )
        )
        # Tools are automatically enabled when attached to the agent
        run_config = RunConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config
        )
    else:
        # Text-only configuration
        run_config = RunConfig(
            response_modalities=["TEXT"]
        )

    # Create LiveRequestQueue
    live_queue = LiveRequestQueue()

    # Store session info with shared interruption flags and custom runner
    active_sessions[user_id] = {
        "session_id": session.id,
        "run_config": run_config,
        "live_queue": live_queue,
        "is_audio": is_audio,
        "runner": session_runner,  # Store the runner for this session
        "should_cancel_output": False,  # Shared flag for stopping audio output
        "user_interrupted": False  # Track if user initiated the interruption
    }

    logger.info(f"Started session for user {user_id}, audio={is_audio}, session_id={session.id}")

    return session.id, run_config, live_queue, session_runner


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, is_audio: str = "true", business_context: Optional[str] = None):
    """WebSocket endpoint following ADK documentation pattern"""

    await websocket.accept()
    logger.info(f"Client #{user_id} connected (audio={is_audio})")

    # Convert is_audio string to boolean
    audio_enabled = is_audio.lower() == "true"

    # Decode business context if provided
    business_context_data = None
    if business_context:
        try:
            import urllib.parse
            decoded_context = urllib.parse.unquote(business_context)
            business_context_data = json.loads(base64.b64decode(decoded_context))
            logger.info(f"📊 Business context received for {user_id}: {business_context_data.get('company_name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error decoding business context: {e}")

    # Initialize ADK session with business context baked into agent instruction
    session_id, run_config, live_queue, session_runner = await start_agent_session(user_id, audio_enabled, business_context_data)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "connected": True,
            "session_id": session_id,
            "audio_enabled": audio_enabled
        })

        # Business context is now BAKED INTO the agent's instruction - no need to inject into conversation memory!
        # The agent already knows the business details from its permanent instruction.

        # Send initial trigger to make the agent start talking first
        # This triggers the agent to greet the user proactively
        if audio_enabled:
            # Send a silent "start" message to trigger the agent's greeting
            initial_trigger = Content(parts=[Part(text="[SESSION_START]")])
            live_queue.send_content(initial_trigger)
            logger.info(f"🎤 Sent initial trigger to agent for user {user_id}")

        # Create concurrent tasks for bidirectional messaging
        # Following the exact pattern from ADK documentation
        tasks = [
            asyncio.create_task(
                agent_to_client_messaging(websocket, live_queue, run_config, user_id, session_id, session_runner)
            ),
            asyncio.create_task(
                client_to_agent_messaging(websocket, live_queue, user_id)
            )
        ]
        
        # Wait for tasks (will complete on disconnect or error)
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        
    finally:
        # Cleanup
        if user_id in active_sessions:
            live_queue.close()
            del active_sessions[user_id]
        logger.info(f"Session ended for user {user_id}")


@app.get("/")
async def root():
    """Redirect to business context page (starting point of the flow)"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/business")

@app.get("/enhanced")
async def enhanced_ui_page():
    """Serve the enhanced UI with tool calls and configuration display"""
    with open("enhanced_ui.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/business")
async def business_context_page():
    """Serve the business context input page"""
    with open("business_context.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/extract-business-context")
async def api_extract_business_context(request: BusinessContextRequest):
    """
    API endpoint to extract business context from a website URL using LLM.

    This uses Gemini to intelligently extract:
    - company_name: str
    - description: str
    - faqs: List[Dict] with 'question' and 'answer' keys (LLM-generated)
    """
    logger.info(f"🌐 Extracting business context from: {request.website_url}")

    context = await extract_business_context(request.website_url)

    return context


@app.get("/health")
async def health_check():
    """Health check endpoint with Phoenix tracing status"""
    phoenix_info = get_phoenix_info()

    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "agent": default_agent.name,
        "model": 'gemini-2.5-flash-native-audio-latest',
        "tools_enabled": len(all_tools),
        "tools": [str(t) for t in all_tools],
        "observability": {
            "phoenix_tracing": phoenix_info['status'],
            "phoenix_enabled": phoenix_info['enabled'],
            "phoenix_project": phoenix_info.get('project_name')
        }
    }

if __name__ == "__main__":
    import uvicorn

    # Display startup information
    print("=" * 60)
    print("🚀 ADK Voice Agent with Tools - Starting Up")
    print("=" * 60)

    # Show Phoenix status
    phoenix_info = get_phoenix_info()
    print(f"\n📊 Observability Status:")
    if phoenix_info['status'] == 'active':
        print(f"   ✅ Phoenix Tracing: ACTIVE")
        print(f"   📁 Project: {phoenix_info['project_name']}")
        print(f"   🔗 Endpoint: {phoenix_info['endpoint']}")
        print(f"   🌐 Dashboard: https://app.phoenix.arize.com")
    elif phoenix_info['status'] == 'disabled':
        print(f"   ⚠️  Phoenix Tracing: DISABLED")
        print(f"   💡 To enable: Set ENABLE_PHOENIX_TRACING=true in .env")
    else:
        print(f"   ⚠️  Phoenix Tracing: MISSING CREDENTIALS")
        print(f"   💡 Add PHOENIX_API_KEY and PHOENIX_COLLECTOR_ENDPOINT to .env")

    # Check SSL for HTTPS
    use_ssl = os.path.exists("cert.pem") and os.path.exists("key.pem")

    print("\n🌐 Server Configuration:")
    if use_ssl:
        print("   Protocol: HTTPS")
        print("   Address: https://localhost:8006")
    else:
        print("   Protocol: HTTP")
        print("   Address: http://localhost:8006")

    print("\n📋 Endpoints:")
    print("   🏠 Start Here: / (redirects to /business)")
    print("   📊 Business Context: /business")
    print("   🎙️ Voice Configuration: /enhanced")
    print("   🔌 WebSocket: /ws/{user_id}")
    print("   ❤️ Health Check: /health")

    print("\n" + "=" * 60)
    print("Starting server...")
    print("=" * 60 + "\n")

    if use_ssl:
        uvicorn.run(app, host="0.0.0.0", port=8006, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8006)