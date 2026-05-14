"""
Configuration module.
Application settings, observability, and agent instructions.
"""
from .settings import Settings, settings
from .observability import (
    setup_phoenix_tracing,
    get_phoenix_info
)
from .agent_instructions import (
    AGENT_INSTRUCTION_TEMPLATE,
    InstructionBuilder,
    instruction_builder
)

__all__ = [
    # Settings
    'Settings',
    'settings',
    # Observability
    'setup_phoenix_tracing',
    'get_phoenix_info',
    # Instructions
    'AGENT_INSTRUCTION_TEMPLATE',
    'InstructionBuilder',
    'instruction_builder',
]
