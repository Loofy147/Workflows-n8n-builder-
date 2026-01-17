"""
LLM Strategy Gateway
Provides a unified interface for switching between Cloud and Local LLMs.
Ensures data privacy and cost optimization for 2026.
"""
import logging
from typing import Dict, List, Any, Optional
from anthropic import AsyncAnthropic
from app.config import settings

logger = logging.getLogger(__name__)

class LLMGateway:
    """
    Manages LLM providers.
    Supports Cloud (Anthropic) and Local (Ollama/vLLM compatible) models.
    """

    def __init__(self):
        self.cloud_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Local endpoint (e.g. running vLLM or Ollama in a sidecar container)
        self.local_endpoint = "http://local-inference:8000/v1"

    async def get_completion(
        self,
        messages: List[Dict],
        system: str = "",
        provider: str = "cloud",
        temperature: float = 0.3
    ) -> str:
        """
        Routes the request to the appropriate provider.
        """
        if provider == "local":
            return await self._get_local_completion(messages, system, temperature)
        else:
            return await self._get_cloud_completion(messages, system, temperature)

    async def _get_cloud_completion(self, messages: List[Dict], system: str, temperature: float) -> str:
        """
        Call Anthropic Claude.
        """
        response = await self.cloud_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            system=system,
            messages=messages,
            temperature=temperature
        )
        return response.content[0].text

    async def _get_local_completion(self, messages: List[Dict], system: str, temperature: float) -> str:
        """
        Call Local LLM (OpenAI compatible API).
        Used for sensitive Algerian data or cost saving.
        """
        # In a real 2026 environment, we would use httpx to call the local_endpoint
        logger.info("Routing to local LLM for privacy-safe processing")
        # Placeholder for actual HTTP call
        return "Local LLM Response Placeholder"

llm_gateway = LLMGateway()
