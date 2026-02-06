import uuid

from fastapi import status

from ai.agent import SchedulingAgent
from ai.models import QNARequestBody, QNAResponseBody
from application.app import app


@app.post(
    "/ai_assistant",
    status_code=status.HTTP_200_OK,
    summary="Chat with Database",
    response_description="Answer from the AI",
)
async def ai_assistant(request: QNARequestBody) -> QNAResponseBody:
    """
    Payload for the endpoint:
    {
        "question": "give me date of birth of Dr. ruso lamba"
        "question": "give me date of birth of Dr. fila delphia"
        "question": "give me date of birth of patient jake funro"
        "question": "what is the speciality of Dr. ruso lamba"
        "question": "Which organ is andre russo associated with?"
        "question": "give me contact details of andre russo"
        "question": "get list of doctors for patient jack kallis"
        "question": "Is Dr. mark ruffello available on 2026-01-30 02:00 for 45 minutes?"
        "question": "create appointment for patient jack kallis on 2026-01-30 at 01:30"
    }
    """
    session_id = request.session_id or str(uuid.uuid4())
    result = SchedulingAgent(
        question=request.question,
        session_id=session_id,
    ).run()
    return {
        "question": request.question,
        "response": result["response"],
        "session_id": result.get("session_id") or session_id,
        "messages": result.get("messages"),
    }
