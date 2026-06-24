from typing import Dict, Any, List
import json
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.provider_abstraction import ProviderFactory, CopilotResponse
from app.copilot.prompt_builder import PromptBuilder
from app.copilot.context_builder import ContextBuilder
from app.copilot.tool_registry import registry

class CopilotEngine:
    def __init__(self):
        self.provider = ProviderFactory.get_provider()
        self.prompt_builder = PromptBuilder()
        self.context_builder = ContextBuilder()

    async def chat(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]], 
        analyst_mode: str, 
        context_ids: Dict[str, str], 
        session: AsyncSession, 
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Main orchestration loop for the Copilot.
        """
        # 1. Preload context
        preloaded_context = await self.context_builder.build_context(context_ids, session, organization_id)
        
        # 2. Build system prompt
        tools_schema = registry.get_tool_schemas()
        system_prompt = self.prompt_builder.build_system_prompt(analyst_mode, tools_schema, preloaded_context)
        
        # 3. Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": user_message})
        
        max_tool_iterations = 5
        tools_used = []
        sources = list(context_ids.values())
        
        for iteration in range(max_tool_iterations):
            logger.info(f"Copilot iteration {iteration+1}")
            
            # Use raw chat format bypassing standard wrapper if we need raw text for custom tool parsing
            # However, BaseProvider.chat handles it. Let's see what it returns.
            # BaseProvider returns CopilotResponse. If it returns an answer, we are done.
            # But what if it wants to use a tool? We need the provider to return raw text or tool calls.
            # Let's adjust: The BaseProvider currently parses CopilotResponse. If it parses a tool_call, we handle it.
            
            try:
                response = await self.provider.chat(messages, tools=[], context_data=None)
            except Exception as e:
                logger.error(f"Provider chat error: {e}")
                return {
                    "answer": "An error occurred communicating with the AI provider.",
                    "tools_used": tools_used,
                    "sources": sources,
                    "confidence": 0
                }
                
            # We hijacked BaseProvider to parse JSON. Let's check if `answer` contains a tool_call signature
            # Actually, the BaseProvider returns answer=raw_text if it fails to parse CopilotResponse.
            # If the LLM outputted `{"tool_call": {...}}`, it won't have `answer`. 
            # We need to refine provider_abstraction to handle this cleanly. 
            # For now, let's assume if "answer" is exactly empty and raw response had "tool_call", we can parse it.
            # Let's read the raw text of the response by modifying BaseProvider slightly. Wait, I can't easily here.
            # Better approach: check if response.answer contains 'tool_call'.
            
            try:
                # Let's see if the LLM outputted the tool call inside the "answer" field due to fallback parsing
                raw_json = json.loads(response.answer) if response.answer.startswith("{") else None
                if raw_json and "tool_call" in raw_json:
                    tool_name = raw_json["tool_call"]["name"]
                    tool_params = raw_json["tool_call"].get("parameters", {})
                    logger.info(f"LLM requested tool: {tool_name}")
                    
                    tool_result = await registry.execute(tool_name, tool_params, session, organization_id)
                    tools_used.append(tool_name)
                    
                    messages.append({
                        "role": "assistant",
                        "content": json.dumps(raw_json)
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Tool Output: {json.dumps(tool_result)}"
                    })
                    continue # loop back and let LLM synthesize
                    
            except json.JSONDecodeError:
                pass
                
            # If it's a properly formatted final response
            if response.answer and response.answer != "No answer provided":
                # Combine tools used and sources
                final_tools = list(set(tools_used + response.tools_used))
                final_sources = list(set(sources + response.sources))
                return {
                    "answer": response.answer,
                    "tools_used": final_tools,
                    "sources": final_sources,
                    "confidence": response.confidence
                }
                
        return {
            "answer": "I reached the maximum number of steps while trying to gather evidence.",
            "tools_used": tools_used,
            "sources": sources,
            "confidence": 0
        }
