import os
from typing import Any

from ai.clients import CohereClient

SESSION_MEMORY: dict[str, list[dict[str, str]]] = {}
MAX_HISTORY = 20


class PolicyAgent:
    def __init__(self, question: str, session_id: str | None = None):
        self.question = question
        self.session_id = session_id
        self.max_steps = int(os.getenv("AI_AGENT_MAX_STEPS", "8"))
        self.client = CohereClient()

    def _trim_history(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        if len(history) <= MAX_HISTORY:
            return history
        return history[-MAX_HISTORY:]

    def run(self) -> dict[str, Any]:
        history = []
        if self.session_id:
            history = list(SESSION_MEMORY.get(self.session_id, []))
        response_text, history = self.client.ask_llm(
            message=self.question,
            chat_history=history,
            max_steps=self.max_steps,
        )
        if self.session_id:
            SESSION_MEMORY[self.session_id] = self._trim_history(history)
        return {
            "response": response_text,
            "messages": history,
            "session_id": self.session_id,
        }
