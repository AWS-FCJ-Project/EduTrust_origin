import logging
from typing import List

from langchain_core.messages import HumanMessage
from langchain_litellm import ChatLiteLLM
from opik import track

from src.app_config import app_config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM client using LiteLLM via LangChain.
    Ho tro sinh cau tra loi tu RAG context.
    """

    def __init__(self):
        # Always use the main project's model for RAG API
        model_name = app_config.AGENT_MODEL
        if not model_name:
            logger.warning("AGENT_MODEL is not set in app_config! Using fallback.")
            model_name = "gpt-4-mini" # default fallback if empty
            
        logger.info(f"Initializing LLMClient with model: {model_name}")
        self.llm = ChatLiteLLM(model=model_name, temperature=0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @track(name="generate_answer")
    def generate_answer(self, query: str, contexts: List[str]) -> str:
        """
        Sinh cau tra loi dua tren query va danh sach context da retrieve.
        """
        context_text = "\n\n".join(contexts)

        prompt = (
            "You are an expert academic assistant.\n"
            "Use ONLY the provided context to answer the question.\n"
            "If the context does not contain enough information, say so clearly.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )

        messages = [
            HumanMessage(content=prompt)
        ]

        logger.info("Sending prompt to LLM...")
        try:
            response = self.llm.invoke(messages)
            
            # Extract content from response
            full_text = str(response.content).strip()
            
            if "Answer:" in full_text:
                return full_text.split("Answer:")[-1].strip()
            return full_text
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "An error occurred while generating the answer."

    def is_loaded(self) -> bool:
        """
        For API usage, the model is always considered 'loaded' or ready
        since there's no local heavy pipeline to load.
        """
        return True
