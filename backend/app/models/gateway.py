"""OpenMesh AI - Unified Model Gateway

Routes requests to different LLM providers with a common interface.
Default: Ollama (local, FREE)
Optional: Claude, GPT, Gemini (free tiers)
"""

import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
import httpx

from app.config import Settings
from app.gateway.models import ModelProvider


class BaseModelProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the model."""
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Stream a response from the model."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_tokens(self) -> float:
        """Cost per 1000 tokens (0.0 for free/local)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model name."""
        pass


class OllamaProvider(BaseModelProvider):
    """Local Ollama provider - COMPLETELY FREE.

    Setup:
    1. Install Ollama: https://ollama.com
    2. Pull a model: ollama pull phi3:3.8b
    3. Start Ollama: ollama serve
    """

    def __init__(self, settings: Settings):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using local Ollama model."""
        full_prompt = ""
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"
        full_prompt += prompt

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Try to list available models
                try:
                    list_resp = await self.client.get(f"{self.base_url}/api/tags")
                    list_resp.raise_for_status()
                    models = list_resp.json()
                    model_names = [m["name"] for m in models.get("models", [])]
                    raise ValueError(f"Model '{self.model}' not found. Available models: {model_names}")
                except Exception:
                    raise ValueError(f"Model '{self.model}' not found in Ollama. Try: docker exec docker-ollama-1 ollama list")
            raise

    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Stream response from Ollama."""
        full_prompt = ""
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"
        full_prompt += prompt

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
            }
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue

    @property
    def cost_per_1k_tokens(self) -> float:
        return 0.0  # FREE

    @property
    def model_name(self) -> str:
        return f"Ollama/{self.model}"


class ClaudeProvider(BaseModelProvider):
    """Anthropic Claude provider (Free tier available)."""

    def __init__(self, settings: Settings):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": self.api_key or "",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Get free credits at console.anthropic.com")

        body = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt

        response = await self.client.post("/v1/messages", json=body)
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        yield await self.generate(prompt, system_prompt)

    @property
    def cost_per_1k_tokens(self) -> float:
        return 0.25  # Haiku is cheap

    @property
    def model_name(self) -> str:
        return f"Claude/{self.model}"


class GPTProvider(BaseModelProvider):
    """OpenAI GPT provider (Free tier available)."""

    def __init__(self, settings: Settings):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={
                "Authorization": f"Bearer {self.api_key or ''}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set. Get free credits at platform.openai.com")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": 2048,
                "temperature": 0.7,
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        yield await self.generate(prompt, system_prompt)

    @property
    def cost_per_1k_tokens(self) -> float:
        return 0.50  # GPT-3.5-turbo

    @property
    def model_name(self) -> str:
        return f"GPT/{self.model}"


class GeminiProvider(BaseModelProvider):
    """Google Gemini provider (Free tier: 1500 requests/day)."""

    def __init__(self, settings: Settings):
        self.api_key = settings.GOOGLE_API_KEY
        self.model = settings.GEMINI_MODEL
        self.client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta",
            timeout=60.0,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set. Get free key at aistudio.google.com")

        contents = [{"role": "user", "parts": [{"text": prompt}]}]

        body = {"contents": contents}
        if system_prompt:
            body["system_instruction"] = {"parts": [{"text": system_prompt}]}

        response = await self.client.post(
            f"/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        yield await self.generate(prompt, system_prompt)

    @property
    def cost_per_1k_tokens(self) -> float:
        return 0.0  # Free tier

    @property
    def model_name(self) -> str:
        return f"Gemini/{self.model}"


class ModelGateway:
    """Unified gateway to all LLM providers.

    Usage:
        gateway = ModelGateway(provider="ollama", settings=settings)
        response = await gateway.generate("Hello!")
    """

    PROVIDERS = {
        ModelProvider.OLLAMA: OllamaProvider,
        ModelProvider.CLAUDE: ClaudeProvider,
        ModelProvider.GPT: GPTProvider,
        ModelProvider.GEMINI: GeminiProvider,
    }

    def __init__(self, provider: str, settings: Settings):
        self.provider_name = provider
        self.settings = settings

        provider_enum = ModelProvider(provider)
        provider_class = self.PROVIDERS[provider_enum]
        self.provider = provider_class(settings)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """Generate response and return with metadata."""
        response_text = await self.provider.generate(prompt, system_prompt)

        # Estimate tokens (rough: 1 token ≈ 4 chars)
        estimated_tokens = (len(prompt) + len(response_text)) // 4
        cost = (estimated_tokens / 1000) * self.provider.cost_per_1k_tokens

        return {
            "response": response_text,
            "model_used": self.provider.model_name,
            "provider": self.provider_name,
            "estimated_tokens": estimated_tokens,
            "cost": round(cost, 6),
        }

    async def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """Stream response."""
        async for chunk in self.provider.generate_stream(prompt, system_prompt):
            yield chunk

    @classmethod
    def list_available(cls, settings: Settings) -> list[dict]:
        """List which providers are configured."""
        available = []
        for provider_enum, provider_class in cls.PROVIDERS.items():
            try:
                instance = provider_class(settings)
                if provider_enum == ModelProvider.OLLAMA:
                    status = "available"
                elif provider_enum == ModelProvider.CLAUDE and settings.ANTHROPIC_API_KEY:
                    status = "available"
                elif provider_enum == ModelProvider.GPT and settings.OPENAI_API_KEY:
                    status = "available"
                elif provider_enum == ModelProvider.GEMINI and settings.GOOGLE_API_KEY:
                    status = "available"
                else:
                    status = "needs_api_key"

                available.append({
                    "id": provider_enum.value,
                    "name": instance.model_name,
                    "status": status,
                    "cost_per_1k": instance.cost_per_1k_tokens,
                })
            except Exception:
                continue
        return available
