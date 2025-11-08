from textwrap import dedent
from agno.agent import Agent
from agno.team import Team

# from agno.models.google import Gemini
from agno.models.openrouter import OpenRouter

# tools
from skills.tools import (
    create_new_tasks,
    list_tasks,
    find_task_by_title,
    find_task_by_id,
    update_task,
    get_models,
)

# prompts
from .prompts import (
    notion_agent_prompt,
    formatter_agent_prompt,
    coordinator_agent_prompt,
    telegram_agent_prompt,
    interpreter_agent_prompt,
)


class AgentFactory:
    def __init__(self, settings):
        self.settings = settings

    def create_interpreter_agent(self):
        interpreter_agent = Agent(
            name="interpreter",
            model=OpenRouter(
                id=self.settings.gemini_pro_model_or,
                api_key=self.settings.open_router_api_key,
                temperature=self.settings.temperature,
                max_tokens=None,
            ),
            instructions=dedent(interpreter_agent_prompt),
            add_datetime_to_instructions=True,
            debug_mode=True,
            show_tool_calls=True,
        )
        return interpreter_agent

    def create_notion_agent(self):
        notion_agent = Agent(
            name="notion",
            model=OpenRouter(
                id=self.settings.gemini_flash_model_or,
                api_key=self.settings.open_router_api_key,
                temperature=self.settings.temperature,
                max_tokens=None,
            ),
            instructions=dedent(notion_agent_prompt),
            tools=[
                list_tasks,
                create_new_tasks,
                find_task_by_title,
                find_task_by_id,
                update_task,
            ],
            add_datetime_to_instructions=True,
            debug_mode=True,
            show_tool_calls=True,
        )

        return notion_agent

    def create_formatter_agent(self):
        formatter_agent = Agent(
            name="formatter",
            model=OpenRouter(
                id=self.settings.gemini_flash_model_or,
                api_key=self.settings.open_router_api_key,
                temperature=self.settings.temperature,
                max_tokens=None,
            ),
            instructions=dedent(formatter_agent_prompt),
            add_datetime_to_instructions=True,
            debug_mode=True,
        )
        return formatter_agent

    def create_telegram_agent(self):
        telegram_agent = Agent(
            name="telegram",
            model=OpenRouter(
                id=self.settings.gemini_flash_model_or,
                api_key=self.settings.open_router_api_key,
                temperature=self.settings.temperature,
                max_tokens=None,
            ),
            instructions=dedent(telegram_agent_prompt),
            tools=[get_models],
            add_datetime_to_instructions=True,
            debug_mode=True,
            show_tool_calls=True,
        )
        return telegram_agent

    def create_coordinator_agent(self):
        notion_agent = self.create_notion_agent()
        notion_agent.name = "notion"
        notion_agent.role = "Especialista em gerenciar as tarefas e projetos no Notion"

        telegram_agent = self.create_telegram_agent()
        telegram_agent.name = "telegram"
        telegram_agent.role = "Executador de ferramentas relacionadas ao Telegram"

        formatter_agent = self.create_formatter_agent()
        formatter_agent.name = "formatter"
        formatter_agent.role = "Especialista em formatação das respostas finais"

        coordinator_agent = Team(
            name="coordinator",
            mode="coordinate",
            model=OpenRouter(
                id=self.settings.gemini_pro_model_or,
                api_key=self.settings.open_router_api_key,
                temperature=self.settings.temperature,
                max_tokens=None,
            ),
            members=[notion_agent, telegram_agent, formatter_agent],
            instructions=dedent(coordinator_agent_prompt),
            debug_mode=True,
            show_tool_calls=True,
        )

        return coordinator_agent

    def get_agent(self, agent_name: str):
        mapper = {
            "interpreter": self.create_interpreter_agent,
            "coordinator": self.create_coordinator_agent,
            "notion": self.create_notion_agent,
            "formatter": self.create_formatter_agent,
            "telegram": self.create_telegram_agent,
        }

        if agent_name not in mapper:
            raise ValueError(f"Unkown Agent - {agent_name}")

        return mapper[agent_name]()
