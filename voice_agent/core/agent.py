"""
Agent factory and management.
Handles creating and configuring ADK agents.
"""
import logging
from typing import Optional, Dict, Any, List, Callable

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from ..config.agent_instructions import instruction_builder
from ..config.settings import settings
from ..tools import tool_registry

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating configured ADK agents."""

    def __init__(
        self,
        model: str = None,
        tools: List[Callable] = None,
        instruction_builder_instance=None
    ):
        self.model = model or settings.model_name
        self.tools = tools or tool_registry.get_all()
        self.instruction_builder = instruction_builder_instance or instruction_builder

    def create(
        self,
        business_context: Optional[Dict[str, Any]] = None,
        name: str = "agent_config_collector"
    ) -> Agent:
        """
        Create an agent with optional business context.

        Args:
            business_context: Business information to include in agent instructions
            name: Name for the agent

        Returns:
            Configured Agent instance
        """
        instruction = self.instruction_builder.build(business_context)

        agent = Agent(
            model=self.model,
            name=name,
            instruction=instruction,
            tools=self.tools
        )

        if business_context:
            company_name = business_context.get('company_name', 'Unknown')
            logger.info(f"Created agent with business context for: {company_name}")
        else:
            logger.info("Created agent without business context (generic)")

        return agent

    def create_runner(
        self,
        agent: Agent,
        app_name: str = "adk_streaming_app"
    ) -> InMemoryRunner:
        """
        Create a runner for an agent.

        Args:
            agent: The agent to run
            app_name: Application name for the runner

        Returns:
            InMemoryRunner instance
        """
        return InMemoryRunner(app_name=app_name, agent=agent)


# Default factory instance
agent_factory = AgentFactory()


def create_agent_with_context(
    business_context: Optional[Dict[str, Any]] = None
) -> Agent:
    """
    Convenience function to create an agent with business context.

    Args:
        business_context: Optional business information

    Returns:
        Configured Agent instance
    """
    return agent_factory.create(business_context)


def get_default_agent() -> Agent:
    """Get or create the default agent without business context."""
    return agent_factory.create()


def get_default_runner() -> InMemoryRunner:
    """Get a runner with the default agent."""
    agent = get_default_agent()
    return agent_factory.create_runner(agent)
