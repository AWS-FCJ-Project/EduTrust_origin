"""
RAG LLM Client - Uses OpenAI GPT API via litellm.
Replaces the local Llama 3.1 8B model from education_chatbot.
"""

import os

import litellm


class RAGLLMClient:
    """LLM client for RAG using OpenAI GPT API via litellm."""

    def __init__(self, model: str = None):
        """
        Initialize the LLM client.

        Args:
            model: Model name (e.g. 'gpt-4.1-nano'). If None, reads from
                   AGENT_MODEL env var, falling back to 'gpt-4.1-nano'.
        """
        self.model = model or os.getenv("AGENT_MODEL", "gpt-4.1-nano")

    async def generate(
        self,
        user_input: str,
        system_prompt: str = None,
        max_tokens: int = 700,
        temperature: float = 0.21,
    ) -> str:
        """
        Generate a response using GPT API (async).

        Args:
            user_input: The user's prompt/question.
            system_prompt: Optional system prompt for context.
            max_tokens: Max tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text response.
        """
        if system_prompt is None:
            system_prompt = "You are a helpful AI assistant."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()

    def generate_sync(
        self,
        user_input: str,
        system_prompt: str = None,
        max_tokens: int = 700,
        temperature: float = 0.21,
    ) -> str:
        """
        Generate a response using GPT API (synchronous).

        Args:
            user_input: The user's prompt/question.
            system_prompt: Optional system prompt for context.
            max_tokens: Max tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Generated text response.
        """
        if system_prompt is None:
            system_prompt = "You are a helpful AI assistant."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        response = litellm.completion(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()
