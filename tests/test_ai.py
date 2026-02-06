from ai import agent as agent_module
from ai import apis as ai_apis


def test_agent_preserves_sensitive_text(monkeypatch):
    class DummyClient:
        def ask_llm(self, message=None, chat_history=None, max_steps=8):
            history = [
                {
                    "role": "USER",
                    "message": "email me at test@example.com or 555-555-1234",
                }
            ]
            return "Contact test@example.com", history

    monkeypatch.setattr(agent_module, "CohereClient", DummyClient)
    agent_module.SESSION_MEMORY.clear()

    agent = agent_module.SchedulingAgent("hello", session_id="s1")
    result = agent.run()
    assert "test@example.com" in result["response"]
    assert "555-555-1234" in result["messages"][0]["message"]


def test_agent_trims_history(monkeypatch):
    class DummyClient:
        def ask_llm(self, message=None, chat_history=None, max_steps=8):
            history = [
                {"role": "USER", "message": f"msg {idx}"}
                for idx in range(agent_module.MAX_HISTORY + 5)
            ]
            return "ok", history

    monkeypatch.setattr(agent_module, "CohereClient", DummyClient)
    agent_module.SESSION_MEMORY.clear()

    agent = agent_module.SchedulingAgent("hello", session_id="s2")
    result = agent.run()
    assert len(result["messages"]) == agent_module.MAX_HISTORY + 5
    assert len(agent_module.SESSION_MEMORY["s2"]) == agent_module.MAX_HISTORY


def test_ai_assistant_endpoint_uses_agent(
    client, monkeypatch, create_user, auth_headers
):
    class DummyAgent:
        def __init__(self, question, session_id=None):
            self.question = question
            self.session_id = session_id

        def run(self):
            return {
                "response": "ok",
                "session_id": self.session_id,
                "messages": [{"role": "CHATBOT", "message": "ok"}],
            }

    monkeypatch.setattr(ai_apis, "SchedulingAgent", DummyAgent)
    user = create_user(username="ai-user", email="ai-user@example.com")
    response = client.post(
        "/ai_assistant",
        json={"question": "Hello"},
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["response"] == "ok"
    assert payload["messages"][0]["message"] == "ok"
