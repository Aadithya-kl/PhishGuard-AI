from typing import List, Dict, Any, Optional
import json
import httpx
from loguru import logger
import google.generativeai as genai
from google.generativeai.types import content_types

from app.config import settings

class CopilotResponse:
    def __init__(self, answer: str, tools_used: List[Dict[str, Any]], sources: List[str], confidence: int):
        self.answer = answer
        self.tools_used = tools_used
        self.sources = sources
        self.confidence = confidence
        
    def to_dict(self):
        return {
            "answer": self.answer,
            "tools_used": self.tools_used,
            "sources": self.sources,
            "confidence": self.confidence
        }

class BaseProvider:
    async def chat(self, messages: List[Dict[str, str]], tools: List[Any], context_data: Dict[str, Any] = None) -> CopilotResponse:
        raise NotImplementedError

class GeminiProvider(BaseProvider):
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-2.5-pro for complex tool use
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.model = None

    async def chat(self, messages: List[Dict[str, str]], tools: List[Any], context_data: Dict[str, Any] = None) -> CopilotResponse:
        if not self.model:
            raise ValueError("GEMINI_API_KEY not configured")
            
        # Convert standard dict messages to Gemini format
        formatted_messages = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                formatted_messages.append({"role": role, "parts": [msg["content"]]})
                
        # For simplicity, we just use the REST-like formatting or Python SDK
        # The prompt builder will handle injecting JSON constraints.
        # Note: Gemini SDK native tool calling is complex to dynamically bind without predefined python functions.
        # We will use prompt-based JSON tool emitting for the unified abstraction unless native tools are strict.
        
        # Since we need tool execution across Ollama/OpenRouter/Gemini, a ReAct prompt approach or OpenAI format is easiest,
        # but the prompt_builder will instruct the LLM to emit a specific JSON schema if it wants to use a tool.
        # For this version, we will rely on structured JSON output from Gemini.
        
        prompt = "System: " + (system_instruction or "") + "\n\n"
        for m in messages:
            if m["role"] != "system":
                prompt += f"{m['role'].capitalize()}: {m['content']}\n"
                
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                )
            )
            text = response.text
            # Try to parse as JSON (assuming prompt builder forces JSON output)
            try:
                # Find JSON block
                if "```json" in text:
                    json_str = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    json_str = text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = text.strip()
                
                parsed = json.loads(json_str)
                # Check if it's a tool call
                if "tool_call" in parsed:
                    # Return it encoded in answer so copilot engine can intercept it
                    return CopilotResponse(answer=json.dumps(parsed), tools_used=[], sources=[], confidence=50)
                    
                return CopilotResponse(
                    answer=parsed.get("answer", "No answer provided"),
                    tools_used=parsed.get("tools_used", []),
                    sources=parsed.get("sources", []),
                    confidence=parsed.get("confidence", 50)
                )
            except json.JSONDecodeError:
                return CopilotResponse(answer=text, tools_used=[], sources=[], confidence=50)
                
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

class OpenRouterProvider(BaseProvider):
    async def chat(self, messages: List[Dict[str, str]], tools: List[Any], context_data: Dict[str, Any] = None) -> CopilotResponse:
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not configured")
            
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "PhishGuard AI Copilot"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": messages,
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            try:
                parsed = json.loads(content)
                return CopilotResponse(
                    answer=parsed.get("answer", "No answer provided"),
                    tools_used=parsed.get("tools_used", []),
                    sources=parsed.get("sources", []),
                    confidence=parsed.get("confidence", 50)
                )
            except json.JSONDecodeError:
                return CopilotResponse(answer=content, tools_used=[], sources=[], confidence=50)

class OllamaProvider(BaseProvider):
    async def chat(self, messages: List[Dict[str, str]], tools: List[Any], context_data: Dict[str, Any] = None) -> CopilotResponse:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "format": "json"
                },
                timeout=60.0
            )
            res.raise_for_status()
            data = res.json()
            content = data["message"]["content"]
            try:
                parsed = json.loads(content)
                return CopilotResponse(
                    answer=parsed.get("answer", "No answer provided"),
                    tools_used=parsed.get("tools_used", []),
                    sources=parsed.get("sources", []),
                    confidence=parsed.get("confidence", 50)
                )
            except json.JSONDecodeError:
                return CopilotResponse(answer=content, tools_used=[], sources=[], confidence=50)


class MockProvider(BaseProvider):
    async def chat(self, messages: List[Dict[str, str]], tools: List[Any], context_data: Dict[str, Any] = None) -> CopilotResponse:
        return CopilotResponse(
            answer="This is a mock Copilot response simulating successful analysis.",
            tools_used=["ioc_lookup"],
            sources=["Simulated Data"],
            confidence=99
        )


class ProviderFactory:
    @staticmethod
    def get_provider() -> BaseProvider:
        if settings.LLM_PROVIDER == "mock":
            if settings.ENVIRONMENT == "production":
                raise ValueError("MockProvider cannot be used in production environments.")
            logger.info("Initializing Mock Copilot Provider")
            return MockProvider()
        # Priority: Gemini -> OpenRouter -> Ollama
        if settings.GEMINI_API_KEY:
            logger.info("Initializing Gemini Copilot Provider")
            return GeminiProvider()
        elif settings.OPENROUTER_API_KEY:
            logger.info("Initializing OpenRouter Copilot Provider")
            return OpenRouterProvider()
        else:
            logger.info("Initializing Ollama Copilot Provider (Fallback)")
            return OllamaProvider()
