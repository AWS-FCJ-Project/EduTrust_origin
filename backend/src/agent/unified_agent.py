from __future__ import annotations

from collections.abc import AsyncIterator

import yaml
from pydantic_ai import Agent
from src.agent.tools import AgentTools
from src.app_config import app_config
from src.conversation.conversation_handler import ConversationHandler
from src.llm import LLM
from src.logger import log_agent_response, log_user_input
from src.schemas.unified_agent_schema import MainAgentDeps, MainAgentStreamEvent
from src.search_services.unified_search import UnifiedSearch
from src.streaming import Streaming
from src.utils import get_current_datetime


class UnifiedAgent:
    """Interface for main agent, sub agents, and execution logic."""

    def __init__(self, llm: LLM, conversation_handler: ConversationHandler) -> None:
        self._llm = llm
        self._conversation_handler = conversation_handler

        self._agents_config: dict = self._load_agents_config()
        self._llms_config: dict = self._load_llms_config()

        self._main_agent: Agent[MainAgentDeps] = self._initialize()

    @property
    def conversation_handler(self) -> ConversationHandler:
        return self._conversation_handler

    def _load_agents_config(self) -> dict:
        with open(app_config.AGENTS_CONFIG_PATH) as file:
            return yaml.safe_load(file)

    def _load_llms_config(self) -> dict:
        with open(app_config.LLMS_CONFIG_PATH) as file:
            return yaml.safe_load(file)

    def _initialize(self) -> Agent[MainAgentDeps]:
        """Build main agent, sub agents, and tools. Returns the wired main agent."""
        main_agent_model_name = app_config.ORCHESTRATOR_MODEL or self._llms_config.get(
            "orchestrator_model"
        )
        sub_agent_model_name = app_config.AGENT_MODEL or self._llms_config.get(
            "agent_model"
        )
        main_agent = Agent(
            self._llm.init_chat_model(main_agent_model_name),
            name="main_agent",
            deps_type=MainAgentDeps,
            instructions=self._agents_config["orchestrator"]["instructions"],
        )

        self._sub_agents = self._create_sub_agents(sub_agent_model_name)

        search_service = UnifiedSearch(tavily_api_key=app_config.TAVILY_API_KEY)
        tools = AgentTools(sub_agents=self._sub_agents, search_service=search_service)
        main_agent.tool(tools.delegate_technical)
        main_agent.tool(tools.delegate_social)
        main_agent.tool(tools.delegate_general)
        main_agent.tool(tools.web_search)
        main_agent.tool(tools.planning)

        return main_agent

    def _create_sub_agents(self, sub_agent_model_name: str) -> dict[str, Agent]:
        """Create all sub agents from config."""
        agent_model = self._llm.init_chat_model(sub_agent_model_name)
        agents_config = self._agents_config
        return {
            "general": Agent(
                agent_model,
                name="general_agent",
                instructions=agents_config["general_agent"]["backstory"],
            ),
            "technical": Agent(
                agent_model,
                name="technical_agent",
                instructions=agents_config["technical_agent"]["backstory"],
            ),
            "social": Agent(
                agent_model,
                name="social_agent",
                instructions=agents_config["social_agent"]["backstory"],
            ),
            "web_search": Agent(
                agent_model,
                name="web_search_agent",
                instructions=agents_config["web_search_agent"]["backstory"],
            ),
        }

    async def ask(self, question: str, conversation_id: str) -> str:
        """Run the main agent and return the full response."""
        deps, prompt = self._build_prompt(question, conversation_id)
        result = await self._main_agent.run(prompt, deps=deps)
        log_agent_response("MainAgent", result.output)
        self._conversation_handler.add_message(
            conversation_id, role="assistant", content=result.output
        )
        self._conversation_handler.get_context(conversation_id, message_limit=10)
        return result.output

    async def ask_stream_with_tool_calls(
        self, question: str, conversation_id: str
    ) -> AsyncIterator[MainAgentStreamEvent]:
        """Stream main agent events: text deltas, tool calls/results, and final answer."""
        deps, prompt = self._build_prompt(question, conversation_id)
        streaming = Streaming(
            orchestrator=self._main_agent,
            deps=deps,
            prompt=prompt,
            conversation_id=conversation_id,
            conversation_handler=self._conversation_handler,
        )
        async for event in streaming.stream_events():
            yield event

    def _build_prompt(
        self, question: str, conversation_id: str
    ) -> tuple[MainAgentDeps, str]:
        """Log input, store message, and assemble prompt with conversation context."""
        log_user_input(question, conversation_id)

        context_messages = self._conversation_handler.get_context(
            conversation_id, message_limit=10
        )
        self._conversation_handler.add_message(
            conversation_id, role="user", content=question
        )
        context_text = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in context_messages
            if message.get("content")
        )
        prompt = (
            f"{get_current_datetime()}\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}"
        )
        deps = MainAgentDeps(
            conversation_id=conversation_id,
            conversation_handler=self._conversation_handler,
        )
        return deps, prompt
