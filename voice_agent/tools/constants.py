"""
Tool configuration constants.
Contains valid options for agent configuration fields.
"""

VALID_PERSONALITIES = [
    "Empathetic and Friendly",
    "Formal and Professional",
    "Salesperson",
    "Fun and Humorous",
    "Casual and Down-To-Earth"
]

VALID_LANGUAGES = [
    "English",
    "Arabic",
    "Hindi",
    "Urdu"
]

VALID_DIALECTS = [
    "Omani",
    "Saudi",
    "Bahraini",
    "Kuwaiti",
    "Qatari",
    "Emirati",
    "Fusha (MSA)"
]

VALID_GENDERS = ["Male", "Female"]

# Field limits
MAX_INTERACTION_STEPS = 10
MIN_INTERACTION_STEPS = 2
MAX_CONVERSATION_EXAMPLES = 20
MAX_HANDOVER_REASONS = 10
MAX_ADDITIONAL_INSTRUCTIONS_LENGTH = 2000
