"""
LLM Client Provider Adapter

Handles communication with different LLM providers (OpenAI, Anthropic, etc.)
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
        
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.3),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class GroqProvider(LLMProvider):
    """Groq provider for fast LLM inference"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("Groq API key not provided")
        
        try:
            import groq
            self.client = groq.AsyncGroq(api_key=self.api_key)
        except ImportError:
            raise ImportError("Groq package not installed. Install with: pip install groq")
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Groq API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


class MockProvider(LLMProvider):
    """Mock provider for testing and development"""
    
    def __init__(self, response_delay: float = 0.1):
        self.response_delay = response_delay
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate mock response for testing"""
        await asyncio.sleep(self.response_delay)
        
        # Simple mock response based on prompt content
        if "No restaurant candidates" in prompt:
            return json.dumps({
                "rankings": [],
                "summary": "No matches found. Consider expanding your search criteria to include nearby locations or different cuisine types.",
                "suggestions": ["Try nearby locations", "Consider different cuisines", "Adjust budget range"]
            })
        else:
            return json.dumps({
                "rankings": [
                    {
                        "rank": 1,
                        "restaurant_name": "Sample Restaurant",
                        "relevance_score": 85,
                        "explanation": "Great match for your preferences with good ratings and reasonable prices.",
                        "highlights": ["Good value", "Popular choice", "Quality food"]
                    }
                ],
                "summary": "Found 1 restaurant that matches your criteria well."
            })


class LLMClient:
    """Main LLM client that manages different providers"""
    
    def __init__(self, provider: Optional[str] = None, **provider_kwargs):
        """
        Initialize LLM client
        
        Args:
            provider: Provider type ('openai', 'anthropic', 'groq', 'mock')
            **provider_kwargs: Provider-specific configuration
        """
        self.provider_name = provider or os.getenv("LLM_PROVIDER", "mock")
        self.provider = self._create_provider(self.provider_name, **provider_kwargs)
    
    def _create_provider(self, provider_name: str, **kwargs) -> LLMProvider:
        """Create provider instance based on type"""
        providers = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "groq": GroqProvider,
            "mock": MockProvider
        }
        
        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")
        
        return providers[provider_name](**kwargs)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using configured provider"""
        try:
            logger.info(f"Generating response using {self.provider_name} provider")
            response = await self.provider.generate_response(prompt, **kwargs)
            logger.info("Response generated successfully")
            return response
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    def switch_provider(self, provider_name: str, **kwargs):
        """Switch to a different provider"""
        self.provider_name = provider_name
        self.provider = self._create_provider(provider_name, **kwargs)
        logger.info(f"Switched to {provider_name} provider")
