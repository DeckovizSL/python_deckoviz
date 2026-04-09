import os
from typing import Dict, Any, List
from collections import defaultdict
from ..llm import GeminiLLM


class ContextualChatAgent:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is required.")

        self.llm = GeminiLLM(model_name=model_name)
        self.memory = defaultdict(list)

    def get_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        return self.memory[user_id][-limit:]

    def save(self, user_id: str, user_msg: str, bot_msg: str):
        self.memory[user_id].append({
            "user": user_msg,
            "bot": bot_msg
        })

    def build_prompt(self, history: List[Dict], message: str) -> str:
        context = ""
        for chat in history:
            context += f"User: {chat['user']}\nAI: {chat['bot']}\n"

        return f"""
You are an intelligent conversational AI for Deckoviz.

Maintain context and continuity in responses.

Conversation history:
{context}

User: {message}
AI:
"""

    def get_response(self, user_id: str, message: str) -> str:
        history = self.get_history(user_id)
        prompt = self.build_prompt(history, message)

        response = self.llm._call(prompt)

        self.save(user_id, message, response)

        return response