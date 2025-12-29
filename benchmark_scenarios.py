test_scenarios = [
    {
        "name": "Happy Path - English Only",
        "user_inputs": [
            "I want to create an agent called Sarah",
            "Make it empathetic and friendly",
            "English only",
            "That's all, thanks"
        ],
        "expected_tools": [
            "get_agent_name",
            "get_agent_gender",
            "get_personality",
            "get_languages",
            "conversation_complete"
        ],
        "expected_output": {
            "agent_name": "Sarah",
            "agent_gender": "Female",
            "personality": "Empathetic and Friendly",
            "languages": ["English"],
            "completed": True
        }
    },
    {
        "name": "Complex - Multiple Languages with Dialect",
        "user_inputs": [
            "Call it Ahmad",
            "Professional style",
            "Arabic and English",
            "Omani dialect please",
            "Done"
        ],
        "expected_tools": [
            "get_agent_name",
            "get_agent_gender",
            "get_personality",
            "get_languages",
            "get_dialect",
            "conversation_complete"
        ],
        "expected_output": {
            "agent_name": "Ahmad",
            "agent_gender": "Male",
            "personality": "Formal and Professional",
            "languages": ["Arabic", "English"],
            "dialect": "Omani",
            "completed": True
        }
    },
    {
        "name": "Error Handling - Invalid Personality",
        "user_inputs": [
            "Name it Alex",
            "Make it super funny and crazy", # Invalid - should be corrected
            "Fun and Humorous",  # Correction
            "English",
            "Done"
        ],
        "should_handle_error": True
    }
]



