from .notion_manager_instructions import notion_agent_prompt
from .formatter_instructions import formatter_agent_prompt
from .coordinator_instructions import coordinator_agent_prompt
from .telegram_instructions import telegram_agent_prompt
from .interpreter_agent_instructions import interpreter_agent_prompt


__all__ = [
    "notion_agent_prompt",
    "formatter_agent_prompt",
    "coordinator_agent_prompt",
    "telegram_agent_prompt",
    "interpreter_agent_prompt",
]
