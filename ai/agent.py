import os
from typing import Any

from ai.clients import CohereClient
from ai.rag import RAGClient

SESSION_MEMORY: dict[str, list[dict[str, str]]] = {}
MAX_HISTORY = 20
POLICY_KEYWORDS = {
    "policy",
    "leave",
    "pto",
    "vacation",
    "sick",
    "holiday",
    "absence",
    "bereavement",
    "maternity",
    "paternity",
    "parental",
    "time off",
    "work from home",
    "remote work",
    "attendance",
    "benefits",
}


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

    def _is_policy_question(self, question: str) -> bool:
        lowered = question.lower()
        return any(keyword in lowered for keyword in POLICY_KEYWORDS)

    def _answer_policy_question(
        self,
        question: str,
        history: list[dict[str, str]],
    ) -> tuple[str, list] | None:
        rag_client = RAGClient()
        top_k = int(os.getenv("POLICY_RAG_TOP_K", "5"))
        matches = rag_client.query_policy_index(question, top_k=top_k)
        if not matches:
            return None

        excerpts = []
        for match in matches:
            title = match.get("document_name") or match.get("policy_name") or "Policy"
            chunk_index = match.get("chunk_index", "unknown")
            text = match.get("text", "")
            if text:
                excerpts.append(f"[{title} - chunk {chunk_index}] {text}")

        if not excerpts:
            return None

        prompt = (
            "You are a policy assistant. Answer the question using only the policy "
            "excerpts below. If the answer is not contained in the excerpts, say you "
            "couldn't find it in the policy documents.\n\n"
            "Policy excerpts:\n"
            f"{os.linesep.join(excerpts)}\n\n"
            f"Question: {question}"
        )
        response_text, history = self.client.ask_llm(
            message=prompt,
            chat_history=history,
            max_steps=self.max_steps,
        )
        return response_text, history

    def run(self) -> dict[str, Any]:
        history = []
        if self.session_id:
            history = list(SESSION_MEMORY.get(self.session_id, []))
        if self._is_policy_question(self.question):
            policy_result = self._answer_policy_question(self.question, history)
            if policy_result:
                response_text, history = policy_result
            else:
                response_text, history = self.client.ask_llm(
                    message=self.question,
                    chat_history=history,
                    max_steps=self.max_steps,
                )
        else:
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
