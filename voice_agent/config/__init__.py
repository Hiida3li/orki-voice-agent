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

    'Settings',
    'settings',

    'setup_phoenix_tracing',
    'get_phoenix_info',

    'AGENT_INSTRUCTION_TEMPLATE',
    'InstructionBuilder',
    'instruction_builder',
]
