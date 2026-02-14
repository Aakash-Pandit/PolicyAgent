import uuid

from fastapi import Depends, Query, status
from sqlalchemy.orm import Session

from ai.agent import PolicyAgent
from ai.db import PolicyEmbedding
from ai.models import QNARequestBody, QNAResponseBody
from application.app import app
from auth.dependencies import require_authenticated_user
from database.db import get_db


@app.post(
    "/ai_assistant",
    status_code=status.HTTP_200_OK,
    summary="Chat with Documents",
    response_description="Answer from the AI",
)
async def ai_assistant(
    request: QNARequestBody,
    current_user=Depends(require_authenticated_user),
) -> QNAResponseBody:
    """
    Payload for the endpoint:
    {
        "question": "give me date of birth of Dr. ruso lamba"
    }
    """
    session_id = request.session_id or str(uuid.uuid4())
    user_id = current_user.user_id if current_user else None
    result = PolicyAgent(
        question=request.question,
        session_id=session_id,
        user_id=user_id,
    ).run()
    return {
        "question": request.question,
        "response": result["response"],
        "session_id": result.get("session_id") or session_id,
        "messages": result.get("messages"),
    }


@app.get("/ai/policy-embeddings")
async def get_policy_embeddings(
    policy_id: str | None = None,
    organization_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(PolicyEmbedding)
    if policy_id:
        query = query.filter(PolicyEmbedding.policy_id == policy_id)
    if organization_id:
        query = query.filter(PolicyEmbedding.organization_id == organization_id)
    rows = (
        query.order_by(PolicyEmbedding.created.desc()).offset(offset).limit(limit).all()
    )
    embeddings = []
    for row in rows:
        item = {
            "id": str(row.id),
            "policy_id": str(row.policy_id),
            "organization_id": str(row.organization_id),
            "policy_name": row.policy_name,
            "description": row.description,
            "document_name": row.document_name,
            "file_path": row.file_path,
            "chunk_index": row.chunk_index,
            "text": row.text,
            "created": row.created,
        }
        embeddings.append(item)
    return {
        "items": embeddings,
        "total": len(embeddings),
        "limit": limit,
        "offset": offset,
    }
