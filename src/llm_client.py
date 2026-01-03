"""
LLM client for BYOM (Bring Your Own Model) support
Supports OpenAI and Anthropic models
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text from prompt"""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Generate text using OpenAI API

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert security analyst helping investigate alerts and incidents."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for more focused, analytical responses
        )

        return response.choices[0].message.content


class AnthropicClient(LLMClient):
    """Anthropic API client"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Anthropic client

        Args:
            api_key: Anthropic API key
            model: Model name to use
        """
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Generate text using Anthropic API

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.3,
            system="You are an expert security analyst helping investigate alerts and incidents.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text


def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    Factory function to create LLM client based on configuration

    Args:
        config: Configuration dictionary with provider, api_key, and model

    Returns:
        LLMClient instance
    """
    provider = config.get("provider", "").lower()

    if provider == "openai":
        return OpenAIClient(
            api_key=config["api_key"],
            model=config.get("model", "gpt-4-turbo-preview")
        )
    elif provider == "anthropic":
        return AnthropicClient(
            api_key=config["api_key"],
            model=config.get("model", "claude-3-5-sonnet-20241022")
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
