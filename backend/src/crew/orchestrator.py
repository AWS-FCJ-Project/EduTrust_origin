from dataclasses import dataclass
from datetime import datetime

import logfire
import yaml
from pydantic_ai import Agent, ToolOutput
from pydantic_ai_litellm import LiteLLMModel
from src.app_config import app_config
from src.logger import log_agent_response, log_user_input
from src.memory.conversation_handler import ConversationHandler
from src.state import get_conversation_handler


@dataclass
class OrchestratorDeps:
    conversation_id: str
    conversation_handler: ConversationHandler


with open(app_config.AGENTS_CONFIG_PATH) as f:
    prompts = yaml.safe_load(f)

with open(app_config.LLMS_CONFIG_PATH) as f:
    llm_config = yaml.safe_load(f)

model_name = app_config.ORCHESTRATOR_MODEL or llm_config.get("orchestrator_model")
model = LiteLLMModel(model_name)

orchestrator = Agent(
    model,
    name="orchestrator",
    deps_type=OrchestratorDeps,
    instructions=prompts["orchestrator"]["instructions"],
    output_type=[
        ToolOutput(
            str,
            name="final_stem_logic_response",
            description="Return STEM/Logic agent's response directly (Math, Physics, Chemistry, Science)",
        ),
        ToolOutput(
            str,
            name="final_humanities_response",
            description="Return Humanities agent's response directly (Literature, History, Social Sciences)",
        ),
        ToolOutput(
            str,
            name="final_quiz_response",
            description="Return quiz agent's response directly",
        ),
        ToolOutput(
            str,
            name="final_general_response",
            description="Return general knowledge agent's response directly",
        ),
        ToolOutput(
            str,
            name="final_web_search_response",
            description="Return web search agent's response directly",
        ),
    ],
)


async def ask(question: str, conversation_id: str) -> str:
    with logfire.span(
        "ask_orchestrator", question=question, conversation_id=conversation_id
    ):
        log_user_input(question, conversation_id)

        handler = get_conversation_handler()
        handler.add_message(conversation_id, role="user", content=question)

        context = handler.get_context(conversation_id, k=10)
        context_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in context if m.get("content")
        )

        deps = OrchestratorDeps(
            conversation_id=conversation_id, conversation_handler=handler
        )
        time_now = datetime.now().astimezone()
        result = await orchestrator.run(
            f"Current date and time: {time_now.strftime('%Y-%m-%d %H:%M:%S %z')}\nContext:\n{context_text}\n\nQuestion: {question}",
            deps=deps,
        )

        answer = result.output
        log_agent_response("Orchestrator", answer)
        handler.add_message(conversation_id, role="assistant", content=answer)
        return answer
